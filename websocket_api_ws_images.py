import sys
import uuid
import json
import os
import time
import random
from websocket import create_connection
from PIL import Image
import io
import requests
import shutil
from time import sleep

# 导入配置
try:
    from config import config
    BASE_DIR = config.BASE_DIR
    server_address = config.COMFYUI_SERVER
    http_server = config.COMFYUI_HTTP
    generated_folder = config.GENERATED_FOLDER
    comfyui_input_dir = config.COMFYUI_INPUT_DIR
    print(f"[CONFIG] Using config file: ComfyUI={config.COMFYUI_DIR}")
except ImportError:
    print("[WARNING] Config file not found, using default settings")
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    server_address = "127.0.0.1:8188"
    http_server = f"http://{server_address}"
    generated_folder = os.path.join(BASE_DIR, 'generated')
    comfyui_input_dir = None

# ─── WORKFLOW TEMPLATE ─────────────────────────────────────────────────────────

NEW_WORKFLOW_TEMPLATE = {
  "44": {
    "inputs": {
      "ckpt_name":"v1-5-pruned-emaonly-fp16.safetensors"  #"cardosAnime_v20.safetensors" #"v1-5-pruned-emaonly-fp16.safetensors"
    },
    "class_type": "CheckpointLoaderSimple",
    "_meta": {
      "title": "Load Checkpoint"
    }
  },
  "45": {
    "inputs": {
      "vae_name": "vae-ft-mse-840000-ema-pruned.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "46": {
    "inputs": {
      "ipadapter_file": "ip-adapter-plus_sd15.safetensors"
    },
    "class_type": "IPAdapterModelLoader",
    "_meta": {
      "title": "IPAdapter Model Loader"
    }
  },
  "47": {
    "inputs": {
      "clip_name": "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors" # "open_clip_model.safetensors"
    },
    "class_type": "CLIPVisionLoader",
    "_meta": {
      "title": "Load CLIP Vision"
    }
  },
  "49": {
    "inputs": {
      "image": "example.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "50": {
    "inputs": {
      "text": "A highly detailed and artistic 3D model created in Blender, featuring a fusion of geometric and organic shapes. Smooth cubes and cylindrical elements are seamlessly merged with fluid, amorphous structures, creating a dynamic interplay of hard edges and flowing forms. The design emphasizes abstraction and avoids any semblance of human-like shapes or recognizable objects. The composition is balanced, with negative space and interlocking shapes that suggest complexity and intrigue. The overall aesthetic is sculptural, with a focus on form and texture, designed to appear as if generated entirely in Blender. The rendering is clean, with soft lighting highlighting the contrasts between geometric precision and organic fluidity.",
      "clip": [
        "44",
        1
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Prompt)"
    }
  },
  "51": {
    "inputs": {
      "text": "Avoid any human-like shapes, faces, or body parts. Exclude sharp spikes, excessive symmetry, and overly mechanical appearances. Avoid using realistic textures or materials that might resemble stone or metal. No baseplates, pedestals, or supporting frames. Keep the composition purely abstract and artistic",
      "clip": [
        "44",
        1
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Prompt)"
    }
  },
  "52": {
    "inputs": {
      "seed": 111525443031905,
      "steps": 25,
      "cfg": 6,
      "sampler_name": "ddim",
      "scheduler": "ddim_uniform",
      "denoise": 1,
      "model": [
        "65",
        0
      ],
      "positive": [
        "50",
        0
      ],
      "negative": [
        "51",
        0
      ],
      "latent_image": [
        "53",
        0
      ]
    },
    "class_type": "KSampler",
    "_meta": {
      "title": "KSampler"
    }
  },
  "53": {
    "inputs": {
      "width": 512,
      "height": 512,
      "batch_size": 4
    },
    "class_type": "EmptyLatentImage",
    "_meta": {
      "title": "Empty Latent Image"
    }
  },
  "54": {
    "inputs": {
      "samples": [
        "52",
        0
      ],
      "vae": [
        "44",
        2
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "55": {
    "inputs": {
      "filename_prefix": "IPAdapter",
      "images": [
        "54",
        0
      ]
    },
    "class_type": "SaveImage",
    "_meta": {
      "title": "Save Image"
    }
  },
  "61": {
    "inputs": {
      "interpolation": "LANCZOS",
      "crop_position": "top",
      "sharpening": 0,
      "image": [
        "49",
        0
      ]
    },
    "class_type": "PrepImageForClipVision",
    "_meta": {
      "title": "Prep Image For ClipVision"
    }
  },
  "62": {
    "inputs": {
      "image": "example.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "63": {
    "inputs": {
      "interpolation": "LANCZOS",
      "crop_position": "top",
      "sharpening": 0,
      "image": [
        "62",
        0
      ]
    },
    "class_type": "PrepImageForClipVision",
    "_meta": {
      "title": "Prep Image For ClipVision"
    }
  },
  "65": {
    "inputs": {
      "weight": 1.0000000000000002,
      "weight_type": "linear",
      "start_at": 0,
      "end_at": 1,
      "embeds_scaling": "V only",
      "model": [
        "44",
        0
      ],
      "ipadapter": [
        "46",
        0
      ],
      "pos_embed": [
        "68",
        0
      ],
      "clip_vision": [
        "47",
        0
      ]
    },
    "class_type": "IPAdapterEmbeds",
    "_meta": {
      "title": "IPAdapter Embeds"
    }
  },
  "66": {
    "inputs": {
      "weight": 1.0000000000000002,
      "ipadapter": [
        "46",
        0
      ],
      "image": [
        "61",
        0
      ],
      "clip_vision": [
        "47",
        0
      ]
    },
    "class_type": "IPAdapterEncoder",
    "_meta": {
      "title": "IPAdapter Encoder"
    }
  },
  "67": {
    "inputs": {
      "weight": 1.0000000000000002,
      "ipadapter": [
        "46",
        0
      ],
      "image": [
        "63",
        0
      ],
      "clip_vision": [
        "47",
        0
      ]
    },
    "class_type": "IPAdapterEncoder",
    "_meta": {
      "title": "IPAdapter Encoder"
    }
  },
  "68": {
    "inputs": {
      "method": "concat",
      "embed1": [
        "66",
        0
      ],
      "embed2": [
        "67",
        0
      ]
    },
    "class_type": "IPAdapterCombineEmbeds",
    "_meta": {
      "title": "IPAdapter Combine Embeds"
    }
  }
}

# ─── HELPERS ───────────────────────────────────────────────────────────────────

def find_comfyui_input_dir():
    """Find the correct ComfyUI input directory."""
    # Use configured path if available
    if 'config' in globals() and comfyui_input_dir and os.path.exists(comfyui_input_dir):
        print(f"[SUCCESS] Using configured ComfyUI input directory: {comfyui_input_dir}")
        return comfyui_input_dir
    
    # Fallback path search
    possible_input_dirs = [
        r"C:\3daiagent\Tools\ComfyUI\input",
        os.path.join(os.path.dirname(BASE_DIR), "ComfyUI", "input"),
        os.path.join(os.path.dirname(BASE_DIR), "Tools", "ComfyUI", "input"),
        r"C:\ComfyUI\input",
        os.path.join(os.path.expanduser("~"), "ComfyUI", "input"),
        os.path.join(BASE_DIR, "input"),
    ]
    
    for input_dir in possible_input_dirs:
        if os.path.exists(input_dir):
            print(f"[SUCCESS] Found ComfyUI input directory: {input_dir}")
            return input_dir
    
    fallback = os.path.join(BASE_DIR, "input")
    os.makedirs(fallback, exist_ok=True)
    print(f"[WARNING] Created fallback input directory: {fallback}")
    return fallback

def test_comfyui_connection():
    """Test if ComfyUI server is running and accessible."""
    try:
        response = requests.get(f"{http_server}/", timeout=5)
        if response.status_code == 200:
            print("[SUCCESS] ComfyUI server is accessible")
            return True
        else:
            print(f"[ERROR] ComfyUI server returned status code {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to connect to ComfyUI server: {e}")
        return False

def clear_comfyui_queue():
    """Clear ComfyUI's queue and interrupt current execution."""
    try:
        print("[QUEUE] Clearing ComfyUI queue...")
        
        # Interrupt current execution
        interrupt_response = requests.post(f"{http_server}/interrupt", timeout=5)
        if interrupt_response.status_code == 200:
            print("[QUEUE] Interrupted current execution")
        
        # Clear the queue
        queue_response = requests.post(f"{http_server}/queue", json={"clear": True}, timeout=5)
        if queue_response.status_code == 200:
            print("[QUEUE] Cleared queue")
        
        time.sleep(1)
        return True
        
    except Exception as e:
        print(f"[QUEUE] Queue clear failed: {e}")
        return False

def clear_comfyui_cache():
    """Clear ComfyUI's internal cache to force image reload."""
    try:
        print("[CACHE] Clearing ComfyUI cache...")
        
        # Clear queue first
        clear_comfyui_queue()
        
        # Try to clear model cache
        response = requests.post(f"{http_server}/free", json={"unload_models": True}, timeout=5)
        if response.status_code == 200:
            print("[CACHE] Model cache cleared")
        else:
            print(f"[CACHE] Model cache clear failed: {response.status_code}")
        
        time.sleep(2)
        return True
    except Exception as e:
        print(f"[CACHE] Cache clear failed: {e}")
        return False

def prepare_image_for_comfyui(image_path):
    """Save image to ComfyUI input directory with a unique name in RGB format."""
    comfyui_input_dir = find_comfyui_input_dir()
    
    timestamp = int(time.time() * 1000)
    random_id = random.randint(1000, 9999)
    unique_filename = f"img_{timestamp}_{random_id}.png"
    dst_path = os.path.join(comfyui_input_dir, unique_filename)

    try:
        # 使用 Pillow 保证格式兼容 ComfyUI，转换为 RGB 并保存
        img = Image.open(image_path).convert("RGB")
        img.save(dst_path)
        print(f"[SUCCESS] Saved image as: {unique_filename}")
        
        # 等待文件系统写入完成，防止 ComfyUI 抢先读取失败
        sleep(1)

        if os.path.exists(dst_path):
            file_size = os.path.getsize(dst_path)
            print(f"[SUCCESS] Verified: {unique_filename} ({file_size} bytes)")
            return unique_filename
        else:
            print(f"[ERROR] Failed to save image: {unique_filename}")
            return None
    except Exception as e:
        print(f"[ERROR] Error saving image for ComfyUI: {e}")
        return None

def cleanup_old_input_files():
    """Clean up old input files after workflow is sent."""
    try:
        comfyui_input_dir = find_comfyui_input_dir()
        existing_files = os.listdir(comfyui_input_dir)
        
        # Only delete files older than 5 minutes
        current_time = time.time()
        for existing_file in existing_files:
            if existing_file.startswith('img_'):
                file_path = os.path.join(comfyui_input_dir, existing_file)
                file_time = os.path.getmtime(file_path)
                if current_time - file_time > 300:  # 5 minutes
                    os.remove(file_path)
                    print(f"[CLEANUP] Deleted old input file: {existing_file}")
    except Exception as e:
        print(f"[WARNING] Could not clean old files: {e}")

def load_and_update_workflow(image1_path, image2_path, positive_prompt, negative_prompt):
    """Load the workflow template and update it with new images and prompts."""
    workflow = json.loads(json.dumps(NEW_WORKFLOW_TEMPLATE))
    
    print(f"[WORKFLOW] Processing images:")
    print(f"[WORKFLOW] Image 1: {os.path.basename(image1_path)}")
    print(f"[WORKFLOW] Image 2: {os.path.basename(image2_path)}")

    if not os.path.exists(image1_path):
        print(f"[ERROR] Image 1 not found: {image1_path}")
        return None
    if not os.path.exists(image2_path):
        print(f"[ERROR] Image 2 not found: {image2_path}")
        return None

    print(f"[WORKFLOW] Preparing images for ComfyUI...")
    image1_filename = prepare_image_for_comfyui(image1_path)
    image2_filename = prepare_image_for_comfyui(image2_path)

    if not image1_filename or not image2_filename:
        print("[ERROR] Failed to prepare images for ComfyUI")
        return None

    workflow["49"]["inputs"]["image"] = image1_filename
    workflow["62"]["inputs"]["image"] = image2_filename
    workflow["50"]["inputs"]["text"] = positive_prompt
    workflow["51"]["inputs"]["text"] = negative_prompt

    unique_prefix = f"IPAdapter_{int(time.time())}"
    workflow["55"]["inputs"]["filename_prefix"] = unique_prefix
    workflow["52"]["inputs"]["seed"] = random.randint(1, 1000000000)

    print(f"[WORKFLOW] Updated workflow:")
    print(f"[WORKFLOW] Node 49 (image1): {workflow['49']['inputs']['image']}")
    print(f"[WORKFLOW] Node 62 (image2): {workflow['62']['inputs']['image']}")
    print(f"[WORKFLOW] Node 55 (prefix): {workflow['55']['inputs']['filename_prefix']}")
    print(f"[WORKFLOW] Node 52 (seed): {workflow['52']['inputs']['seed']}")

    return workflow

def send_workflow_http(workflow):
    """Send the workflow using the HTTP API."""
    try:
        clear_comfyui_cache()
        
        client_id = str(uuid.uuid4())
        print(f"[HTTP] Generated client_id: {client_id}")
        
        payload = {
            "prompt": workflow,
            "client_id": client_id
        }
        
        print(f"[HTTP] Sending workflow to ComfyUI...")
        response = requests.post(
            f"{http_server}/prompt",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            prompt_id = result.get('prompt_id')
            print(f"[HTTP] Workflow queued successfully with prompt_id: {prompt_id}")
            return client_id, prompt_id
        else:
            print(f"[ERROR] Failed to queue workflow: {response.status_code}")
            print(f"[ERROR] Response: {response.text}")
            return client_id, None
            
    except Exception as e:
        print(f"[ERROR] Error sending workflow: {e}")
        return None, None

def check_http_history(expected_prefix=None):
    """Check the ComfyUI history API for recent outputs."""
    try:
        print(f"[HISTORY] Checking ComfyUI history...")
        if expected_prefix:
            print(f"[HISTORY] Looking for images with prefix: {expected_prefix}")
        
        response = requests.get(f"{http_server}/history", timeout=10)
        
        if response.status_code != 200:
            print(f"[ERROR] Failed to get history: {response.status_code}")
            return None
            
        history = response.json()
        print(f"[HISTORY] Got history with {len(history)} entries")
        
        if not history:
            print("[HISTORY] History is empty")
            return None
        
        # Sort history entries by timestamp (newest first)
        sorted_history = sorted(history.items(), key=lambda x: x[0], reverse=True)
        
        # Look through the most recent entries to find our specific workflow
        for history_key, history_entry in sorted_history[:10]:  # Check top 10 most recent
            print(f"[HISTORY] Checking history entry: {history_key}")
            
            # Check if this entry has outputs
            if 'outputs' not in history_entry:
                print(f"[HISTORY] Entry {history_key} has no outputs")
                continue
            
            # Look for images in this entry
            images = []
            for node_id, output in history_entry.get('outputs', {}).items():
                if 'images' in output:
                    for img_info in output['images']:
                        if 'filename' in img_info:
                            filename = img_info.get('filename')
                            
                            # If we have an expected prefix, only accept matching images
                            if expected_prefix and not filename.startswith(expected_prefix):
                                print(f"[HISTORY] Skipping {filename} - doesn't match prefix {expected_prefix}")
                                continue
                            
                            # Only process IPAdapter images
                            if filename.startswith('IPAdapter_'):
                                subfolder = img_info.get('subfolder', '')
                                folder_type = img_info.get('type', 'output')
                                
                                if subfolder:
                                    image_url = f"{http_server}/view?filename={subfolder}/{filename}&type={folder_type}"
                                else:
                                    image_url = f"{http_server}/view?filename={filename}&type={folder_type}"
                                
                                images.append({
                                    'filename': filename,
                                    'url': image_url,
                                    'node_id': node_id,
                                    'history_key': history_key
                                })
                                print(f"[HISTORY] Found matching image: {filename}")
            
            if images:
                print(f"[HISTORY] Found {len(images)} matching images in entry {history_key}")
                return download_images_from_history(images)
        
        print("[HISTORY] No matching IPAdapter images found in recent history")
        return None
            
    except Exception as e:
        print(f"[ERROR] Error checking history: {e}")
        return None

def download_images_from_history(images):
    """Download images from ComfyUI history."""
    os.makedirs(generated_folder, exist_ok=True)
    
    downloaded = []
    current_timestamp = int(time.time())
    
    for i, img_info in enumerate(images):
        try:
            print(f"[DOWNLOAD] Downloading: {img_info['filename']} from history {img_info['history_key']}")
            response = requests.get(img_info['url'], timeout=15)
            
            if response.status_code == 200:
                # Create unique filename with current timestamp
                dst_name = f"generated_{current_timestamp}_{i}_{img_info['filename']}"
                dst_path = os.path.join(generated_folder, dst_name)
                
                with open(dst_path, 'wb') as f:
                    f.write(response.content)
                    
                print(f"[SUCCESS] Saved: {dst_name}")
                downloaded.append(dst_path)
                
                # Save the first image as latest_image.png for compatibility
                if i == 0:
                    latest_path = os.path.join(generated_folder, 'latest_image.png')
                    with open(latest_path, 'wb') as f:
                        f.write(response.content)
                    print(f"[SUCCESS] Also saved as: latest_image.png")
            else:
                print(f"[ERROR] Failed to download: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Error downloading image: {e}")
    
    return downloaded

# ─── ENTRYPOINT ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("[ERROR] Usage: python websocket_api_ws_images.py <image1> <image2> <positive_prompt> <negative_prompt>")
        sys.exit(1)

    img1, img2, pos_prompt, neg_prompt = sys.argv[1:5]
    
    print(f"[START] Starting ComfyUI workflow with:")
    print(f"[START] Image 1: {os.path.basename(img1)}")
    print(f"[START] Image 2: {os.path.basename(img2)}")

    if not test_comfyui_connection():
        print("[ERROR] Failed to connect to ComfyUI server.")
        sys.exit(1)

    workflow = load_and_update_workflow(img1, img2, pos_prompt, neg_prompt)
    
    if not workflow:
        print("[ERROR] Failed to prepare workflow.")
        sys.exit(1)

    print(f"[HTTP] Sending workflow to ComfyUI...")
    client_id, prompt_id = send_workflow_http(workflow)
    
    if not prompt_id:
        print("[ERROR] Failed to queue workflow.")
        sys.exit(1)

    print(f"[WAIT] Waiting 45 seconds for ComfyUI to process...")
    time.sleep(45)
    
    # Clean up old input files now that workflow is submitted
    cleanup_old_input_files()
    
    # Get the expected prefix from our workflow
    expected_prefix = workflow["55"]["inputs"]["filename_prefix"]
    print(f"[RESULT] Looking for images with prefix: {expected_prefix}")
    
    print(f"[RESULT] Checking for generated images...")
    downloaded_images = check_http_history(expected_prefix)
    
    if downloaded_images:
        print(f"[SUCCESS] Generated {len(downloaded_images)} images:")
        for img in downloaded_images:
            print(f"[SUCCESS] {os.path.basename(img)}")
    else:
        print(f"[WARNING] No new images found.")