import pandas as pd
import hashlib
import os
from datetime import datetime

class AuthManager:
    def __init__(self, users_file='users.csv'):
        self.users_file = users_file
        self.init_users_file()
    
    def init_users_file(self):
        if not os.path.exists(self.users_file):
            df = pd.DataFrame(columns=['username', 'password_hash', 'email', 'created_at'])
            df.to_csv(self.users_file, index=False)
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def load_users(self):
        return pd.read_csv(self.users_file)
    
    def save_users(self, df):
        df.to_csv(self.users_file, index=False)
    
    def user_exists(self, username):
        users_df = self.load_users()
        return username in users_df['username'].values
    
    def email_exists(self, email):
        users_df = self.load_users()
        return email in users_df['email'].values
    
    def create_user(self, username, password, email):
        if self.user_exists(username):
            return False, "Username already exists"
        
        if self.email_exists(email):
            return False, "Email already registered"
        
        users_df = self.load_users()
        
        new_user = pd.DataFrame({
            'username': [username],
            'password_hash': [self.hash_password(password)],
            'email': [email],
            'created_at': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        })
        
        users_df = pd.concat([users_df, new_user], ignore_index=True)
        self.save_users(users_df)
        
        return True, "Account created successfully"
    
    def authenticate(self, username, password):
        users_df = self.load_users()
        
        user = users_df[users_df['username'] == username]
        
        if user.empty:
            return False, "Username not found"
        
        stored_hash = user.iloc[0]['password_hash']
        
        if self.hash_password(password) == stored_hash:
            return True, "Login successful"
        else:
            return False, "Incorrect password"
    
    def get_user_info(self, username):
        users_df = self.load_users()
        user = users_df[users_df['username'] == username]
        
        if not user.empty:
            return user.iloc[0].to_dict()
        return None
