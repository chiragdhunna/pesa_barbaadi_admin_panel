# Pesa Barbaadi Admin Panel

An admin panel for managing trip expenses in the Pesa Barbaadi application.

## Features

- User management (add, edit, disable/enable, delete users)
- Trip management (create, view details, edit, delete trips)
- Entry management (log fuel expenses, edit, delete entries)
- Dashboard with metrics (total users, trips, entries, total spent) and recent activity
- Data export (Excel, PDF, CSV) for trips with date filtering
- Balance calculation and settlement tracking

## Prerequisites

- Python 3.8 or higher
- Firebase project with Firestore and Authentication enabled
- Firebase service account key (JSON file)

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pesa_barbaadi_admin_panel
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up Firebase**
   - Go to your Firebase project console
   - Navigate to Project Settings > Service Accounts
   - Click "Generate new private key" to download a service account key JSON file
   - Alternatively, if you already have a service account key, note its path
   - Create a `.streamlit/secrets.toml` file in the project root with the following content:
     ```toml
     FIREBASE_SERVICE_ACCOUNT_PATH = "path/to/your/serviceAccountKey.json"
     ADMIN_USERNAME = "your_admin_username"
     ADMIN_PASSWORD = "your_admin_password"
     ```
   - Replace `"path/to/your/serviceAccountKey.json"` with the actual path to your service account key file.
   - Set your desired admin username and password for login.

6. **Initialize Firebase in your project (if not already done)**
   - Ensure your Firebase project has Firestore Database enabled (in Native mode)
   - Enable Firebase Authentication (we use email/password for admin login, but the service account is used for backend access)

## Running the Application

1. **Make sure your virtual environment is activated**
2. **Run the Streamlit app**
   ```bash
   streamlit run app.py
   ```
3. **Open your browser** to the URL shown in the terminal (usually http://localhost:8501)
4. **Login** using the admin credentials set in `.streamlit/secrets.toml`

## Project Structure

```
pesa_barbaadi_admin_panel/
│
├── app.py                  # Main entry point, handles authentication and navigation
├── requirements.txt        # Python dependencies
├── README.md               # This file
│
├── .streamlit/
│   └── secrets.toml        # Firebase and admin credentials (not in repo, add your own)
│
├── pages/                   # Streamlit pages for different sections
│   ├── 1_Dashboard.py       # Dashboard with metrics and recent activity
│   ├── 2_Users.py           # User management
│   ├── 3_Trips.py           # Trip management
│   ├── 4_Entries.py         # Entry management (fuel logs)
│   └── 5_Export.py          # Data export functionality
│
├── services/                # Service modules for Firebase and business logic
│   ├── __init__.py
│   ├── firebase_service.py  # Firebase initialization
│   ├── balance_service.py   # Balance calculation logic
│   └── export_service.py    # Export to Excel, PDF, CSV
│
├── .gitignore               # Git ignore rules
├── err.log                  # Error log (generated)
└── out.log                  # Output log (generated)
```

## Firebase Configuration

### Required Firestore Collections

The application expects the following Firestore structure:

- `trips` (collection)
  - Each trip document contains:
    - `members` (map): userID -> displayName
    - `balance` (map): userID -> net amount (positive = owed money, negative = owes money)
    - `createdAt` (timestamp)
    - `total_spent` (number, computed)
    - `entry_count` (number, computed)

- `trips/{tripId}/entries` (subcollection)
  - Each entry document contains:
    - `paidByUid` (string): userID of who paid
    - `paidByName` (string): display name of payer (denormalized for convenience)
    - `amount` (number): amount spent
    - `date` (timestamp or date): date of expense
    - `type` (string): "full" or "partial"
    - `note` (string): optional note
    - `createdAt` (timestamp): when entry was created

### Required Indexes

For the dashboard's recent activity query to work, you need to create a **collection group index**:

1. Go to Firebase Console > Firestore > Indexes
2. Click "+ Create Index"
3. Configure:
   - Collection ID: `entries`
   - Field Path: `createdAt`
   - Order: `Descending`
   - Query scope: **Collection group**
4. Click "Create"

Without this index, the recent activity section on the dashboard will fail to load.

## Deployment

### Streamlit Community Cloud

1. Push this repository to GitHub
2. Go to [Streamlit Community Cloud](https://streamlit.io/cloud)
3. Click "New app"
4. Select your repository, branch, and set the main file as `app.py`
5. In the secrets section, add:
   ```toml
   FIREBASE_SERVICE_ACCOUNT_PATH = "/mnt/secrets/serviceAccountKey.json"
   ADMIN_USERNAME = "your_username"
   ADMIN_PASSWORD = "your_password"
   ```
6. Upload your Firebase service account key as a secret file (name it `serviceAccountKey.json`)
7. Deploy

### Vercel

To deploy on Vercel, you need to set the following environment variables in your Vercel project settings:

- `FIREBASE_SERVICE_ACCOUNT_JSON`: The entire Firebase service account key as a JSON string.
  You can obtain this by copying the contents of your serviceAccountKey.json file.
- `ADMIN_USERNAME`: Your admin username for login.
- `ADMIN_PASSWORD`: Your admin password for login.

**Note:** The application will automatically use these environment variables if they are set. If not, it will fall back to looking for `FIREBASE_SERVICE_ACCOUNT_PATH` in Streamlit secrets (for local development) and then environment variables.

### Other Platforms (Heroku, Docker, etc.)

The application can be deployed anywhere that supports Python and Streamlit. You'll need to:
- Set environment variables for the secrets (or use a secrets.toml file)
- Ensure the service account key is accessible

## Dependencies

See `requirements.txt` for the full list. Key dependencies include:
- streamlit
- firebase-admin
- openpyxl (for Excel export)
- reportlab (for PDF export)
- pandas (for data manipulation)

## Troubleshooting

### Firebase Initialization Errors

- **Service account not found**: Double-check the path in `.streamlit/secrets.toml`
- **Permission denied**: Ensure the service account has Firestore and Auth permissions
- **Firebase app already initialized**: This is handled by the `@st.cache_resource` decorator

### Query Errors

- **Missing index**: The Firebase console will provide a link to create the missing index when a query fails due to missing index
- **Permission denied**: Check Firestore rules - the service account needs read/write access

### Login Issues

- Ensure you've set `ADMIN_USERNAME` and `ADMIN_PASSWORD` in `.streamlit/secrets.toml`
- Passwords are case-sensitive

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Streamlit](https://streamlit.io)
- Uses [Firebase](https://firebase.google.com) for backend services