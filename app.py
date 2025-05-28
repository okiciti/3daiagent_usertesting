from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import subprocess
import uuid
import sys
import time

# 导入配置
from config import config

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# 使用配置中的路径
UPLOAD_FOLDER = config.UPLOAD_FOLDER
GENERATED_FOLDER = config.GENERATED_FOLDER
SCRIPT_PATH = config.SCRIPT_PATH
PYTHON_EXECUTABLE = config.PYTHON_EXECUTABLE

@app.route('/test')
def test():
    """测试端点，显示配置信息"""
    return jsonify({
        'message': 'Flask server is working with auto-config!',
        'config': {
            'upload_folder': UPLOAD_FOLDER,
            'generated_folder': GENERATED_FOLDER,
            'script_path': SCRIPT_PATH,
            'python_executable': PYTHON_EXECUTABLE,
            'comfyui_server': config.COMFYUI_HTTP,
            'comfyui_input_dir': config.COMFYUI_INPUT_DIR
        }
    })

@app.route('/upload', methods=['POST'])
def upload_images():
    """Upload endpoint to handle image file uploads."""
    print("DEBUG: Upload endpoint called")
    files = request.files.getlist('images')
    print(f"DEBUG: Received {len(files)} files")
    
    if not files or len(files) != 2:
        print("ERROR: Invalid number of files")
        return jsonify({'error': 'Please upload exactly two images.'}), 400

    image_paths = []
    for i, file in enumerate(files):
        if not file.filename:
            print(f"ERROR: File {i+1} has no filename")
            return jsonify({'error': f'File {i+1} has no filename.'}), 400
            
        # Check file extension
        file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        if file_ext not in ['png', 'jpg', 'jpeg']:
            print(f"ERROR: Invalid file format: {file.filename}")
            return jsonify({'error': f'Invalid file format: {file.filename}. Only PNG, JPG, JPEG allowed.'}), 400
        
        # Generate unique filename
        filename = f"{uuid.uuid4()}.{file_ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save the file
        try:
            file.save(filepath)
            image_paths.append(filepath)
            print(f"DEBUG: Saved file {i+1}: {filepath}")
        except Exception as e:
            print(f"ERROR: Failed to save file {i+1}: {e}")
            return jsonify({'error': f'Failed to save file {i+1}: {str(e)}'}), 500

    print(f"DEBUG: Returning image paths: {image_paths}")
    return jsonify({'imagePaths': image_paths})

@app.route('/generate', methods=['POST'])
def generate_image():
    """Generate endpoint to process images with ComfyUI."""
    print("DEBUG: Generate endpoint called")
    print(f"DEBUG: Python executable: {PYTHON_EXECUTABLE}")
    print(f"DEBUG: Script path: {SCRIPT_PATH}")
    
    # Parse JSON data
    try:
        data = request.json
        print(f"DEBUG: Parsed JSON data: {data}")
    except Exception as e:
        print(f"ERROR: Failed to parse JSON: {e}")
        return jsonify({'error': 'Invalid JSON data'}), 400
    
    # Extract required fields
    images = data.get('images')
    positive_prompt = data.get('positivePrompt')
    negative_prompt = data.get('negativePrompt')

    print(f"DEBUG: Images: {images}")
    print(f"DEBUG: Positive prompt: {positive_prompt}")
    print(f"DEBUG: Negative prompt: {negative_prompt}")

    # Validate input
    if not images or len(images) != 2:
        print("ERROR: Invalid images - need exactly 2 images")
        return jsonify({'error': 'Invalid input: need exactly 2 images.'}), 400
        
    if not positive_prompt or not negative_prompt:
        print("ERROR: Missing prompts")
        return jsonify({'error': 'Invalid input: missing prompts.'}), 400

    # Check if image files exist
    for i, img_path in enumerate(images):
        if not os.path.exists(img_path):
            print(f"ERROR: Image {i+1} not found: {img_path}")
            return jsonify({'error': f'Image {i+1} not found: {img_path}'}), 400

    # Record files before generation
    files_before = set()
    if os.path.exists(GENERATED_FOLDER):
        files_before = set(os.listdir(GENERATED_FOLDER))
    print(f"DEBUG: Files in generated folder before: {files_before}")

    # Clean old files automatically
    if os.path.exists(GENERATED_FOLDER):
        old_files = [f for f in os.listdir(GENERATED_FOLDER) if f.endswith('.png')]
        if len(old_files) > 5:  # Keep only 5 most recent
            old_files.sort(key=lambda x: os.path.getmtime(os.path.join(GENERATED_FOLDER, x)), reverse=True)
            files_to_delete = old_files[5:]  # Delete all but 5 newest
            for old_file in files_to_delete:
                try:
                    os.remove(os.path.join(GENERATED_FOLDER, old_file))
                    print(f"DEBUG: 🗑️ Deleted old file: {old_file}")
                except Exception as e:
                    print(f"DEBUG: Failed to delete {old_file}: {e}")

    # Prepare subprocess command using configured Python executable
    cmd = [PYTHON_EXECUTABLE, SCRIPT_PATH, images[0], images[1], positive_prompt, negative_prompt]
    print(f"DEBUG: Calling subprocess with: {cmd}")

    # Call the Python script to process the images
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=300  # 5 minute timeout
        )
    except subprocess.TimeoutExpired:
        print("ERROR: Subprocess timed out after 5 minutes")
        return jsonify({'error': 'Image generation timed out'}), 500
    except Exception as e:
        print(f"ERROR: Subprocess failed: {e}")
        return jsonify({'error': f'Failed to run image generation: {str(e)}'}), 500

    print(f"DEBUG: Subprocess return code: {result.returncode}")
    print(f"DEBUG: Subprocess stdout: {result.stdout}")
    if result.stderr:
        print(f"DEBUG: Subprocess stderr: {result.stderr}")

    if result.returncode != 0:
        print(f"ERROR: Script failed with error: {result.stderr}")
        return jsonify({'error': f'Failed to generate image: {result.stderr}'}), 500

    # Find newly generated images
    if os.path.exists(GENERATED_FOLDER):
        all_png_files = [f for f in os.listdir(GENERATED_FOLDER) if f.endswith('.png')]
        
        if all_png_files:
            # Sort by modification time (newest first)
            all_png_files.sort(key=lambda x: os.path.getmtime(os.path.join(GENERATED_FOLDER, x)), reverse=True)
            
            # Get files created in the last 30 seconds
            fresh_files = []
            current_time = time.time()
            for file in all_png_files:
                file_path = os.path.join(GENERATED_FOLDER, file)
                file_time = os.path.getmtime(file_path)
                time_diff = current_time - file_time
                
                if time_diff < 30:  # Files created in last 30 seconds
                    fresh_files.append(file)
                    print(f"DEBUG: Found fresh file: {file} (age: {time_diff:.1f}s)")
            
            if fresh_files:
                print(f"DEBUG: ✅ Found {len(fresh_files)} fresh generated files")
                
                # Return all fresh generated images
                image_paths = [f"generated/{file}" for file in fresh_files]
                return jsonify({
                    'generatedImagePaths': image_paths,  # Return array of all images
                    'generatedImagePath': image_paths[0]  # Keep backward compatibility with single image
                })

    # Fallback
    return jsonify({'error': 'No generated images found'}), 500

@app.route('/generated/<filename>')
def serve_generated(filename):
    """Serve generated images from the generated folder."""
    print(f"DEBUG: Serving file: {filename}")
    
    # Add cache-busting headers to prevent browser caching
    response = send_from_directory(GENERATED_FOLDER, filename)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/config')
def show_config():
    """显示当前配置"""
    return jsonify({
        'status': 'running',
        'config_valid': config.validate_setup(),
        'base_dir': config.BASE_DIR,
        'upload_folder': UPLOAD_FOLDER,
        'generated_folder': GENERATED_FOLDER,
        'python_executable': PYTHON_EXECUTABLE,
        'script_path': SCRIPT_PATH,
        'comfyui_dir': config.COMFYUI_DIR,
        'comfyui_input_dir': config.COMFYUI_INPUT_DIR,
        'comfyui_server': config.COMFYUI_HTTP,
    })

if __name__ == '__main__':
    print("🚀 启动 Flask 服务器...")
    
    # 验证配置
    if not config.validate_setup():
        print("❌ 配置验证失败，请检查配置!")
        print("\n📋 建议运行以下命令:")
        print(config.get_install_commands())
        sys.exit(1)
    
    print("✅ 配置验证通过，启动服务器...")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)