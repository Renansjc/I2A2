#!/usr/bin/env python3
"""
MVP Setup Script - Sistema Simplificado de Análise Fiscal
Leverages existing code from alternative project with Supabase integration
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header():
    print("=" * 60)
    print("🚀 MVP Sistema Simplificado de Análise Fiscal")
    print("   Leveraging Alternative Project + Supabase")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python 3.11+ is available"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11+ is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def check_node_version():
    """Check if Node.js 18+ is available"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip().replace('v', '')
            major_version = int(version.split('.')[0])
            if major_version >= 18:
                print(f"✅ Node.js {version} detected")
                return True
            else:
                print(f"❌ Node.js 18+ required, found {version}")
                return False
    except FileNotFoundError:
        print("❌ Node.js not found")
        return False

def setup_backend():
    """Setup backend environment"""
    print("\n📦 Setting up Backend...")
    
    # Change to backend directory
    os.chdir('backend')
    
    # Create virtual environment
    print("   Creating virtual environment...")
    subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
    
    # Determine activation script path
    if os.name == 'nt':  # Windows
        activate_script = 'venv\\Scripts\\activate'
        pip_path = 'venv\\Scripts\\pip'
        python_path = 'venv\\Scripts\\python'
    else:  # Unix/Linux/macOS
        activate_script = 'venv/bin/activate'
        pip_path = 'venv/bin/pip'
        python_path = 'venv/bin/python'
    
    # Install dependencies
    print("   Installing dependencies...")
    subprocess.run([pip_path, 'install', '-r', 'requirements.txt'], check=True)
    
    # Install spaCy Portuguese model
    print("   Installing spaCy Portuguese model...")
    try:
        subprocess.run([python_path, '-m', 'spacy', 'download', 'pt_core_news_sm'], check=True)
        print("   ✅ spaCy Portuguese model installed")
    except subprocess.CalledProcessError:
        print("   ⚠️  spaCy model installation failed (optional)")
    
    # Copy .env.example to .env if it doesn't exist
    if not os.path.exists('.env'):
        shutil.copy('.env.example', '.env')
        print("   📝 Created .env file from template")
        print("   ⚠️  Please edit .env with your configuration")
    
    os.chdir('..')
    print("   ✅ Backend setup complete")

def setup_frontend():
    """Setup frontend environment"""
    print("\n🎨 Setting up Frontend...")
    
    # Change to frontend directory
    os.chdir('frontend')
    
    # Install dependencies
    print("   Installing dependencies...")
    subprocess.run(['npm', 'install'], check=True)
    
    # Copy .env.example to .env if it doesn't exist
    if not os.path.exists('.env'):
        shutil.copy('.env.example', '.env')
        print("   📝 Created .env file from template")
        print("   ⚠️  Please edit .env with your API configuration")
    
    os.chdir('..')
    print("   ✅ Frontend setup complete")

def print_next_steps():
    """Print next steps for the user"""
    print("\n🎯 Next Steps:")
    print()
    print("1. Configure Environment Variables:")
    print("   📝 Edit backend/.env with your Supabase and OpenAI credentials")
    print("   📝 Edit frontend/.env with your API base URL")
    print()
    print("2. Start the Backend:")
    print("   cd backend")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("   python main.py")
    print()
    print("3. Start the Frontend (in another terminal):")
    print("   cd frontend")
    print("   npm run dev")
    print()
    print("4. Access the Application:")
    print("   🌐 Frontend: http://localhost:3000")
    print("   🔧 Backend API: http://localhost:8000")
    print("   📚 API Docs: http://localhost:8000/docs")
    print()
    print("5. Test with Sample XML:")
    print("   📁 Use files from xml_nf/ directory for testing")
    print()
    print("🚀 MVP Features Available:")
    print("   • XML Upload with drag-and-drop")
    print("   • 3-Agent Processing Pipeline (XML → Categorization → Insights)")
    print("   • Executive Dashboard with real data")
    print("   • Supabase integration for data storage")
    print("   • Real-time processing status")
    print()

def main():
    """Main setup function"""
    print_header()
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    if not check_node_version():
        sys.exit(1)
    
    print("\n🔍 Prerequisites check passed!")
    
    try:
        # Setup backend
        setup_backend()
        
        # Setup frontend
        setup_frontend()
        
        # Print next steps
        print_next_steps()
        
        print("✅ MVP Setup Complete!")
        print("   Ready to process Brazilian fiscal documents with AI agents!")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()