import streamlit as st
import os
import threading
import time
import urllib.request
import urllib.error
from streamlit.web import bootstrap as st_bootstrap

# Set Streamlit server port from Vercel's PORT environment variable if available
PORT = int(os.environ.get("PORT", 8501))
if "PORT" in os.environ:
    os.environ["STREAMLIT_SERVER_PORT"] = str(PORT)

# Configure Streamlit to run in headless mode (no browser) and disable unnecessary features
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["STREAMLIT_SERVER_ENABLE_CORS"] = "false"
os.environ["STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION"] = "false"
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

# Global variable to hold the Streamlit server thread
_streamlit_thread = None
_server_started = False
_server_start_lock = threading.Lock()

def run_streamlit():
    """Run Streamlit app in headless mode. This function blocks."""
    # Configure Streamlit options
    sys_argv = [
        "streamlit",
        "run",
        __file__,
        "--server.port", str(PORT),
        "--server.headless", "true",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false",
        "--browser.gatherUsageStats", "false",
    ]
    # Bootstrap Streamlit with our arguments
    st_bootstrap.run(sys_argv, flag_options={})

def start_streamlit_server():
    """Start the Streamlit server in a background thread if not already started."""
    global _streamlit_thread, _server_started
    with _server_start_lock:
        if not _server_started:
            _streamlit_thread = threading.Thread(target=run_streamlit, daemon=True)
            _streamlit_thread.start()
            _server_started = True
            # Give the server a moment to start
            time.sleep(2)

def login_page():
    st.set_page_config(
        page_title="Pesa Barbaadi Admin",
        page_icon="⛽",
        layout="wide"
    )

    # Get admin credentials from secrets or environment variables
    try:
        ADMIN_USERNAME = st.secrets["ADMIN_USERNAME"]
    except (KeyError, FileNotFoundError):
        ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")

    try:
        ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
    except (KeyError, FileNotFoundError):
        ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

    # Create centered column
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Large fuel emoji and title
        st.markdown("<h1 style='text-align: center;'>⛽</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>Pesa Barbaadi Admin</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888;'>Admin interface for managing trip expenses</p>", unsafe_allow_html=True)

    # Login form
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            # Compare with secrets or environment variables
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Invalid username or password")

# Check authentication status
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login_page()
    st.stop()
else:
    st.success("✓ Logged in as admin")
    st.info("Use the sidebar to navigate between pages.")

    # Logout button in sidebar
    if st.sidebar.button("🚪 Logout"):
        st.session_state["authenticated"] = False
        st.rerun()

# Start Streamlit server when module is imported (for Vercel)
start_streamlit_server()

# WSGI app object for Vercel Python builder
def app(environ, start_response):
    # Proxy request to the local Streamlit server
    try:
        # Construct the target URL
        target_url = f"http://127.0.0.1:{PORT}{environ.get('PATH_INFO', '')}"
        if environ.get('QUERY_STRING'):
            target_url += f"?{environ['QUERY_STRING']}"

        # Prepare headers to forward (excluding hop-by-hop headers)
        headers = {}
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                header_name = key[5:].replace('_', '-')
                if header_name.lower() not in ('host', 'connection', 'keep-alive',
                                             'proxy-authenticate', 'proxy-authorization',
                                             'te', 'trailers', 'transfer-encoding', 'upgrade'):
                    headers[header_name] = value
            elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                header_name = key.replace('_', '-')
                headers[header_name] = value

        # Read request body if present
        request_body = None
        if environ.get('REQUEST_METHOD') in ('POST', 'PUT', 'PATCH'):
            try:
                request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            except (ValueError):
                request_body_size = 0
            if request_body_size > 0:
                request_body = environ['wsgi.input'].read(request_body_size)

        # Make the request to Streamlit server
        req = urllib.request.Request(
            target_url,
            data=request_body,
            headers=headers,
            method=environ.get('REQUEST_METHOD', 'GET')
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                status = f"{response.status} {response.reason}"
                response_headers = dict(response.getheaders())
                # Remove hop-by-hop headers from response
                for hop in ('connection', 'keep-alive', 'proxy-authenticate',
                           'proxy-authorization', 'te', 'trailers', 'transfer-encoding', 'upgrade'):
                    response_headers.pop(hop, None)
                # Convert headers to list of tuples
                headers_list = [(k, v) for k, v in response_headers.items()]
                start_response(status, headers_list)
                return [response.read()]
        except urllib.error.URLError as e:
            # If Streamlit server is not ready, return 503
            status = '503 Service Unavailable'
            headers = [('Content-Type', 'text/plain')]
            start_response(status, headers)
            return [b'Streamlit server is starting up. Please try again in a few seconds.']
    except Exception as e:
        # Fallback error
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'text/plain')]
        start_response(status, headers)
        return [f'Internal Server Error: {str(e)}'.encode()]

# For local testing: if run directly, start Streamlit server and serve requests via the same WSGI app
if __name__ == "__main__":
    # When run directly, we want to run Streamlit normally (not as a proxy)
    # But we can also run the WSGI app using a simple server for testing
    from wsgiref.simple_server import make_server
    print(f"Serving on http://127.0.0.1:{PORT}")
    start_streamlit_server()  # This will start the background thread
    httpd = make_server('', PORT, app)
    print("Serving HTTP on port", PORT)
    # Handle requests until interrupted
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        httpd.shutdown()