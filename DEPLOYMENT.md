# 🚀 Deployment Guide for Social Listening Tool

## 📋 Prerequisites

Before deploying, ensure you have:
- Python 3.8+ installed
- MySQL database (local or cloud)
- Git repository with your code

## 🎯 Deployment Options

### Option 1: Streamlit Cloud (Recommended - Free)

**Pros:** Free, easy, automatic deployments
**Cons:** Limited customization, requires public repository

#### Steps:
1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/social-listening-tool.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set main file path: `social_listening_app.py`
   - Click "Deploy"

3. **Configure Environment Variables**
   - In Streamlit Cloud dashboard, go to "Settings"
   - Add environment variables:
     ```
     MYSQL_HOST=your_mysql_host
     MYSQL_USER=your_mysql_user
     MYSQL_PASSWORD=your_mysql_password
     MYSQL_DATABASE=social_listening
     ```

### Option 2: Railway (Easy - Free Tier)

**Pros:** Free tier, easy deployment, good performance
**Cons:** Limited free tier usage

#### Steps:
1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Deploy**
   ```bash
   railway login
   railway init
   railway up
   ```

3. **Add Environment Variables**
   ```bash
   railway variables set MYSQL_HOST=your_host
   railway variables set MYSQL_USER=your_user
   railway variables set MYSQL_PASSWORD=your_password
   railway variables set MYSQL_DATABASE=social_listening
   ```

### Option 3: Heroku (Popular - Free Tier Discontinued)

**Pros:** Well-established platform
**Cons:** No free tier anymore

#### Steps:
1. **Create Procfile**
   ```
   web: streamlit run social_listening_app.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. **Deploy**
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

### Option 4: VPS/Cloud Server (Advanced)

**Pros:** Full control, customizable
**Cons:** Requires server management

#### Steps:
1. **Set up Ubuntu/Debian server**
2. **Install dependencies**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip nginx mysql-server
   ```

3. **Clone and setup**
   ```bash
   git clone https://github.com/yourusername/social-listening-tool.git
   cd social-listening-tool
   pip3 install -r requirements.txt
   ```

4. **Create systemd service**
   ```bash
   sudo nano /etc/systemd/system/social-listening.service
   ```
   
   Add:
   ```ini
   [Unit]
   Description=Social Listening Tool
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/social-listening-tool
   Environment="PATH=/home/ubuntu/social-listening-tool/venv/bin"
   ExecStart=/home/ubuntu/social-listening-tool/venv/bin/streamlit run social_listening_app.py --server.port=8501 --server.address=0.0.0.0
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

5. **Start service**
   ```bash
   sudo systemctl enable social-listening
   sudo systemctl start social-listening
   ```

## 🗄️ Database Setup

### Local MySQL
```sql
-- Run database_setup.sql in your MySQL server
mysql -u root -p < database_setup.sql
```

### Cloud MySQL Options:
- **PlanetScale** (Free tier available)
- **AWS RDS** (Pay per use)
- **Google Cloud SQL** (Pay per use)
- **DigitalOcean Managed MySQL** (Fixed price)

## 🔧 Environment Variables

Create a `.env` file or set these in your deployment platform:

```env
MYSQL_HOST=localhost
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=social_listening
MYSQL_PORT=3306
```

## 📁 File Structure for Deployment

```
social_listening_tool/
├── social_listening_app.py    # Main app
├── login_ui.py               # Login interface
├── database.py               # Database operations
├── requirements.txt          # Python dependencies
├── database_setup.sql       # Database schema
├── README.md                # Documentation
├── DEPLOYMENT.md            # This file
└── .gitignore              # Git ignore file
```

## 🚨 Important Notes

1. **Database Security**: Use strong passwords and restrict database access
2. **Environment Variables**: Never commit sensitive data to Git
3. **HTTPS**: Enable SSL for production deployments
4. **Monitoring**: Set up logging and monitoring for production
5. **Backups**: Regular database backups are essential

## 🆘 Troubleshooting

### Common Issues:
1. **Database Connection**: Check MySQL credentials and network access
2. **Port Issues**: Ensure port 8501 (or configured port) is open
3. **Dependencies**: Verify all packages are in requirements.txt
4. **Memory**: Some AI models require significant RAM

### Debug Commands:
```bash
# Check if app runs locally
streamlit run social_listening_app.py

# Test database connection
python -c "from database import Database; db = Database(); print('DB OK')"

# Check dependencies
pip list | grep -E "(streamlit|pandas|requests)"
```

## 📞 Support

For deployment issues:
1. Check the logs in your deployment platform
2. Verify environment variables are set correctly
3. Test database connectivity
4. Ensure all dependencies are installed 

## 🔧 **Step 15: Create Configuration File**

### **Step 15.1: Create Database Configuration**
In your Hostinger File Manager, in the `social_listening_tool` folder:

1. **Create a new file** called `config.py`
2. **Add this content** (replace with your actual database credentials):

```python
# Database configuration for Hostinger
DB_CONFIG = {
    'host': 'localhost',
    'user': 'u681900159_social_user',
    'password': 'your_actual_password_here',
    'database': 'u681900159_social_listeni',
    'port': 3306
}
```

### **Step 15.2: Update Database Connection**
Now we need to update the `database.py` file to use your Hostinger configuration.

**In File Manager:**
1. **Open `database.py`**
2. **Find the `connect` method**
3. **Replace the database connection with your Hostinger credentials**

**Let me know when you've created the `config.py` file with your database credentials!**

Then I'll help you update the database connection and test the application.

**What's your database password?** (I need it to help you configure the connection properly) 