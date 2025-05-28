import os
import sys
import platform

class Config:
    def __init__(self):
        # Project root directory
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        
        # Basic folders
        self.UPLOAD_FOLDER = os.path.join(self.BASE_DIR, 'uploads')
        self.GENERATED_FOLDER = os.path.join(self.BASE_DIR, 'generated')
        self.SCRIPT_PATH = os.path.join(self.BASE_DIR, 'websocket_api_ws_images.py')
        
        # ComfyUI configuration
        self.COMFYUI_SERVER = "127.0.0.1:8188"
        self.COMFYUI_HTTP = f"http://{self.COMFYUI_SERVER}"
        
        # Auto-detect paths
        self.COMFYUI_DIR = r"C:\Users\nomy_\Downloads\ComfyUI\ComfyUI_windows_portable"   # self.find_comfyui_dir()
        self.COMFYUI_INPUT_DIR = os.path.join(self.COMFYUI_DIR, "ComfyUI\input")
        self.PYTHON_EXECUTABLE = self.find_python_executable()
        
        # Create necessary directories
        self.create_directories()
        
        # Print configuration info
        self.print_config()
    
    def find_comfyui_dir(self):
        """Automatically find ComfyUI installation directory"""
        possible_paths = [
            # Windows common paths
            r"C:\ComfyUI",
            r"C:\3daiagent\Tools\ComfyUI",
            r"C:\Users\{}\ComfyUI".format(os.getenv('USERNAME', '')),
            r"C:\Program Files\ComfyUI",
            
            # Relative paths
            os.path.join(self.BASE_DIR, "ComfyUI"),
            os.path.join(os.path.dirname(self.BASE_DIR), "ComfyUI"),
            os.path.join(os.path.dirname(self.BASE_DIR), "Tools", "ComfyUI"),
            
            # User directory
            os.path.join(os.path.expanduser("~"), "ComfyUI"),
            os.path.join(os.path.expanduser("~"), "Desktop", "ComfyUI"),
            os.path.join(os.path.expanduser("~"), "Documents", "ComfyUI"),
        ]
        
        # Add user-specific paths
        username = os.getenv('USERNAME') or os.getenv('USER') or 'user'
        possible_paths.extend([
            f"C:\\Users\\{username}\\ComfyUI",
            f"C:\\Users\\{username}\\Desktop\\ComfyUI",
            f"C:\\Users\\{username}\\Documents\\ComfyUI",
        ])
        
        print("[SEARCH] Looking for ComfyUI installation directory...")
        for path in possible_paths:
            if os.path.exists(path):
                # Validate if it's a valid ComfyUI directory
                if self.is_valid_comfyui_dir(path):
                    print(f"[SUCCESS] Found ComfyUI directory: {path}")
                    return path
                else:
                    print(f"[WARNING] Found directory but not valid ComfyUI: {path}")
        
        print("[ERROR] ComfyUI directory not found")
        return None
    
    def is_valid_comfyui_dir(self, path):
        """Validate if it's a valid ComfyUI directory"""
        required_files = ['main.py', 'execution.py']
        required_dirs = ['models', 'input', 'output']
        
        # Check required files
        for file in required_files:
            if not os.path.exists(os.path.join(path, file)):
                return False
        
        # Check required directories
        for dir in required_dirs:
            if not os.path.exists(os.path.join(path, dir)):
                return False
        
        return True
    
    def find_comfyui_input_dir(self):
        """Find ComfyUI input directory"""
        if self.COMFYUI_DIR:
            input_dir = os.path.join(self.COMFYUI_DIR, 'input')
            if os.path.exists(input_dir):
                print(f"[SUCCESS] Found ComfyUI input directory: {input_dir}")
                return input_dir
        
        # Fallback input directory paths
        fallback_paths = [
            os.path.join(self.BASE_DIR, "input"),
            r"C:\ComfyUI\input",
            r"C:\3daiagent\Tools\ComfyUI\input",
        ]
        
        for path in fallback_paths:
            if os.path.exists(path):
                print(f"[SUCCESS] Using fallback input directory: {path}")
                return path
        
        # Create local input directory
        fallback = os.path.join(self.BASE_DIR, "input")
        os.makedirs(fallback, exist_ok=True)
        print(f"[WARNING] Created local input directory: {fallback}")
        return fallback
    
    def find_python_executable(self):
        """Find the correct Python executable"""
        # Prioritize virtual environment Python
        venv_paths = [
            os.path.join(self.BASE_DIR, 'venv', 'Scripts', 'python.exe'),  # Windows
            os.path.join(self.BASE_DIR, 'venv', 'bin', 'python'),          # Linux/Mac
            os.path.join(self.BASE_DIR, '.venv', 'Scripts', 'python.exe'), # Windows alt
            os.path.join(self.BASE_DIR, '.venv', 'bin', 'python'),         # Linux/Mac alt
        ]
        
        for path in venv_paths:
            if os.path.exists(path):
                print(f"[SUCCESS] Using virtual environment Python: {path}")
                return path
        
        # Use system Python
        system_python = sys.executable
        print(f"[WARNING] Using system Python: {system_python}")
        return system_python
    
    def create_directories(self):
        """Create necessary directories"""
        directories = [
            self.UPLOAD_FOLDER,
            self.GENERATED_FOLDER,
        ]
        
        if self.COMFYUI_INPUT_DIR:
            directories.append(self.COMFYUI_INPUT_DIR)
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def print_config(self):
        """Print current configuration"""
        print("\n" + "="*60)
        print("Current Configuration:")
        print("="*60)
        print(f"Project Directory: {self.BASE_DIR}")
        print(f"Upload Directory: {self.UPLOAD_FOLDER}")
        print(f"Generated Directory: {self.GENERATED_FOLDER}")
        print(f"Python Executable: {self.PYTHON_EXECUTABLE}")
        print(f"Script Path: {self.SCRIPT_PATH}")
        print(f"ComfyUI Directory: {self.COMFYUI_DIR}")
        print(f"ComfyUI Input Directory: {self.COMFYUI_INPUT_DIR}")
        print(f"ComfyUI Server: {self.COMFYUI_HTTP}")
        print("="*60)
    
    def validate_setup(self):
        """Validate if setup is correct"""
        issues = []
        
        # Check Python executable
        if not os.path.exists(self.PYTHON_EXECUTABLE):
            issues.append(f"[ERROR] Python executable does not exist: {self.PYTHON_EXECUTABLE}")
        
        # Check script file
        if not os.path.exists(self.SCRIPT_PATH):
            issues.append(f"[ERROR] Script file does not exist: {self.SCRIPT_PATH}")
        
        # Check ComfyUI directory
        if not self.COMFYUI_DIR:
            issues.append("[ERROR] ComfyUI installation directory not found")
        elif not os.path.exists(self.COMFYUI_DIR):
            issues.append(f"[ERROR] ComfyUI directory does not exist: {self.COMFYUI_DIR}")
        
        # Check input directory
        if not os.path.exists(self.COMFYUI_INPUT_DIR):
            issues.append(f"[ERROR] ComfyUI input directory does not exist: {self.COMFYUI_INPUT_DIR}")
        
        if issues:
            print("\n[ERROR] Found the following issues:")
            for issue in issues:
                print(f"   {issue}")
            return False
        else:
            print("\n[SUCCESS] All configuration checks passed!")
            return True
    
    def get_install_commands(self):
        """Generate installation commands"""
        commands = [
            "# Create and activate virtual environment",
            "python -m venv venv",
            "venv\\Scripts\\activate  # Windows",
            "# or source venv/bin/activate  # Linux/Mac",
            "",
            "# Install dependencies",
            "pip install flask flask-cors websocket-client pillow requests",
            "",
            "# Verify installation",
            f'python -c "import config; config.Config().validate_setup()"'
        ]
        return "\n".join(commands)

# Create global configuration instance
config = Config()

# Export common configurations
BASE_DIR = config.BASE_DIR
UPLOAD_FOLDER = config.UPLOAD_FOLDER
GENERATED_FOLDER = config.GENERATED_FOLDER
SCRIPT_PATH = config.SCRIPT_PATH
COMFYUI_HTTP = config.COMFYUI_HTTP
COMFYUI_INPUT_DIR = config.COMFYUI_INPUT_DIR
PYTHON_EXECUTABLE = config.PYTHON_EXECUTABLE

if __name__ == "__main__":
    print("Configuration Check Tool")
    if config.validate_setup():
        print("\n[SUCCESS] System configuration is correct, ready to start!")
    else:
        print("\n[INFO] Suggested installation commands:")
        print(config.get_install_commands())