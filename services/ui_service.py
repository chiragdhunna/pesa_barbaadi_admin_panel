import streamlit as st

def show_centered_spinner(message="Initializing application..."):
    """
    Renders a premium, centered CSS loading spinner that matches the theme's primary color.
    """
    return st.markdown(f"""
        <div class="centered-spinner-container">
            <div class="custom-spinner"></div>
            <div class="spinner-message">{message}</div>
        </div>
        <style>
        .centered-spinner-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 40vh;
        }}
        .custom-spinner {{
            border: 4px solid rgba(255, 255, 255, 0.1);
            width: 48px;
            height: 48px;
            border-radius: 50%;
            border-left-color: #5B7FFF; /* matching primary color */
            animation: spin 1s linear infinite;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        .spinner-message {{
            margin-top: 16px;
            font-family: inherit;
            color: #8E9AA8;
            font-size: 15px;
            font-weight: 500;
        }}
        </style>
    """, unsafe_allow_html=True)

def show_dashboard_shimmer():
    """
    Renders a shimmer skeleton mimicking the Dashboard page (4 cards + recent activity table).
    """
    return st.markdown("""
        <style>
        @keyframes shimmer {
            0% { background-position: -468px 0; }
            100% { background-position: 468px 0; }
        }
        .shimmer-card {
            background: #161B28;
            border-radius: 10px;
            padding: 24px;
            border: 1px solid #222a3d;
            height: 110px;
        }
        .shimmer-table {
            background: #161B28;
            border-radius: 10px;
            padding: 28px;
            border: 1px solid #222a3d;
            margin-top: 28px;
        }
        .shimmer-bar {
            background: #1c2333;
            background-image: linear-gradient(to right, #1c2333 0%, #2b354d 20%, #1c2333 40%, #1c2333 100%);
            background-repeat: no-repeat;
            background-size: 800px 104px;
            animation: shimmer 1.5s infinite linear;
            border-radius: 4px;
        }
        </style>
        <div style="display: flex; gap: 18px; margin-bottom: 28px;">
            <div class="shimmer-card" style="flex: 1;">
                <div class="shimmer-bar" style="height: 14px; width: 60%; margin-bottom: 16px;"></div>
                <div class="shimmer-bar" style="height: 28px; width: 40%;"></div>
            </div>
            <div class="shimmer-card" style="flex: 1;">
                <div class="shimmer-bar" style="height: 14px; width: 60%; margin-bottom: 16px;"></div>
                <div class="shimmer-bar" style="height: 28px; width: 40%;"></div>
            </div>
            <div class="shimmer-card" style="flex: 1;">
                <div class="shimmer-bar" style="height: 14px; width: 60%; margin-bottom: 16px;"></div>
                <div class="shimmer-bar" style="height: 28px; width: 40%;"></div>
            </div>
            <div class="shimmer-card" style="flex: 1;">
                <div class="shimmer-bar" style="height: 14px; width: 60%; margin-bottom: 16px;"></div>
                <div class="shimmer-bar" style="height: 28px; width: 40%;"></div>
            </div>
        </div>
        <div class="shimmer-table">
            <div class="shimmer-bar" style="height: 24px; width: 25%; margin-bottom: 28px;"></div>
            <div class="shimmer-bar" style="height: 18px; width: 100%; margin-bottom: 14px;"></div>
            <div class="shimmer-bar" style="height: 18px; width: 100%; margin-bottom: 14px;"></div>
            <div class="shimmer-bar" style="height: 18px; width: 100%; margin-bottom: 14px;"></div>
            <div class="shimmer-bar" style="height: 18px; width: 100%; margin-bottom: 14px;"></div>
        </div>
    """, unsafe_allow_html=True)

def show_table_shimmer(rows=5):
    """
    Renders a shimmer skeleton mimicking a content table / grid.
    """
    row_html = "".join([
        '<div class="shimmer-bar" style="height: 38px; width: 100%; margin-bottom: 14px;"></div>'
        for _ in range(rows)
    ])
    return st.markdown(f"""
        <style>
        @keyframes shimmer {{
            0% {{ background-position: -468px 0; }}
            100% {{ background-position: 468px 0; }}
        }}
        .shimmer-container {{
            background: #161B28;
            border-radius: 10px;
            padding: 28px;
            border: 1px solid #222a3d;
        }}
        .shimmer-bar {{
            background: #1c2333;
            background-image: linear-gradient(to right, #1c2333 0%, #2b354d 20%, #1c2333 40%, #1c2333 100%);
            background-repeat: no-repeat;
            background-size: 800px 104px;
            animation: shimmer 1.5s infinite linear;
            border-radius: 4px;
        }}
        </style>
        <div class="shimmer-container">
            <div class="shimmer-bar" style="height: 24px; width: 30%; margin-bottom: 28px;"></div>
            {row_html}
        </div>
    """, unsafe_allow_html=True)
