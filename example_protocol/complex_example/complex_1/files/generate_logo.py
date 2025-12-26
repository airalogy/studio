"""
🧬 星际联邦生物实验协议 - Logo & Banner 生成器

使用 AI 生成精英科研风格的 Logo 和 Banner。

风格要求：
- 精英主义科研风，不要廉价科技感
- 简洁、专业、学术气质
- 参考 Nature/Science/Cell 期刊的设计语言
- 配色：深蓝、金色、白色为主

使用方式：
    export YUNWU_API_KEY="your-api-key"
    python complex_example/files/generate_logo.py
"""

import os
import sys
import json
import time
import base64
import requests
from pathlib import Path

# ============================================================
# 配置
# ============================================================

API_KEY = os.environ.get("YUNWU_API_KEY", "sk-uIR61bwuv96qGMDa9RY2J91np9JKDINdrCQfdknTfIQHqm71")
API_HOST = "yunwu.ai"
OUTPUT_DIR = Path(__file__).parent

# Logo 和 Banner 的 Prompt
ASSETS = {
    "logo": {
        "prompt": """Design a minimalist, elegant scientific research logo.

Style: Premium academic institution aesthetic, inspired by Nature/Science journal design language.

Elements:
- A stylized DNA double helix or molecular structure, abstracted into clean geometric lines
- Subtle quantum/atomic orbital rings integrated elegantly
- NO text, pure symbol/icon only

Color palette:
- Deep navy blue (#1a365d) as primary
- Metallic gold accent (#c9a227)
- Clean white highlights

Design principles:
- Minimalist and sophisticated, NOT flashy sci-fi
- Could belong to Harvard, MIT, or Max Planck Institute
- Timeless elegance over trendy effects
- High contrast, works on both light and dark backgrounds
- Vector-style clean edges

Output: Square format, centered composition, transparent or white background.""",
        "aspect_ratio": "1:1",
        "filename": "logo.png"
    },
    
    "logo_dark": {
        "prompt": """Design a minimalist, elegant scientific research logo on dark background.

Style: Premium academic institution aesthetic, inspired by Nature/Science journal design language.

Elements:
- A stylized DNA double helix or molecular structure, abstracted into clean geometric lines
- Subtle quantum/atomic orbital rings integrated elegantly
- NO text, pure symbol/icon only

Color palette:
- Soft white/silver (#f0f4f8) as primary symbol color
- Metallic gold accent (#c9a227)
- Deep navy background (#0d1b2a)

Design principles:
- Minimalist and sophisticated, NOT flashy sci-fi
- Could belong to Harvard, MIT, or Max Planck Institute
- Timeless elegance over trendy effects
- Clean vector-style edges

Output: Square format, centered composition, dark navy background.""",
        "aspect_ratio": "1:1",
        "filename": "logo_dark.png"
    },
    
    "banner": {
        "prompt": """Design a professional scientific research banner/header image.

Style: Elite academic publication aesthetic, like a Nature journal article header.

Composition (left to right):
- Left 1/4: Abstract molecular/cellular visualization, soft and elegant
- Center: Clean space for text overlay (leave mostly empty)
- Right 1/4: Subtle scientific imagery (microscopy texture, data visualization hint)

Visual elements:
- Soft, out-of-focus microscopy imagery of cells in background
- Delicate molecular structure lines
- Subtle grid or graph paper texture
- NO flashy effects, NO neon colors

Color palette:
- Deep navy blue (#1a365d) dominant
- Soft teal accent (#2c7a7b)
- Warm gold highlights (#c9a227)
- Cream/off-white (#faf5eb) for light areas

Text overlay area:
- Leave center-left area clean for title text
- Suggested text placement zone should be obvious

Design principles:
- Sophisticated and understated
- Academic gravitas, NOT corporate tech
- Could be a Cell journal cover
- Elegant gradient transitions
- Professional photography quality feel

Output: Wide banner format (4:1 ratio), suitable for document header.""",
        "aspect_ratio": "21:9",
        "filename": "banner.png"
    }
}


# ============================================================
# API 调用
# ============================================================

def generate_image(prompt: str, aspect_ratio: str = "1:1") -> bytes | None:
    """使用 Gemini 生成图像"""
    if not API_KEY:
        print("   ❌ 未设置 YUNWU_API_KEY 环境变量")
        return None
    
    url = f"https://{API_HOST}/v1beta/models/gemini-3-pro-image-preview:generateContent"
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {
                "aspectRatio": aspect_ratio,
                "imageSize": "1K"
            }
        }
    }
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"   🔄 正在生成...")
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        
        # 提取图像数据
        if 'candidates' in result:
            for candidate in result['candidates']:
                if 'content' in candidate and 'parts' in candidate['content']:
                    for part in candidate['content']['parts']:
                        if 'inlineData' in part:
                            image_data = part['inlineData'].get('data')
                            if image_data:
                                return base64.b64decode(image_data)
        
        print(f"   ⚠️ 响应中未找到图像数据")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ 请求失败: {e}")
        return None


def save_image(data: bytes, filename: str):
    """保存图像"""
    filepath = OUTPUT_DIR / filename
    with open(filepath, 'wb') as f:
        f.write(data)
    size_kb = len(data) / 1024
    print(f"   ✅ 已保存: {filename} ({size_kb:.1f} KB)")


# ============================================================
# 主函数
# ============================================================

def main():
    print("\n" + "="*60)
    print("🧬 星际联邦生物实验协议 - Logo & Banner 生成器")
    print("   风格: 精英主义科研风 (Nature/Science aesthetic)")
    print("="*60)
    
    if not API_KEY:
        print("\n❌ 请设置环境变量 YUNWU_API_KEY")
        print("   export YUNWU_API_KEY='your-api-key'")
        sys.exit(1)
    
    print(f"\n📁 输出目录: {OUTPUT_DIR}")
    print(f"🔑 API Key: {API_KEY[:15]}...")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 生成指定的素材，或全部
    targets = sys.argv[1:] if len(sys.argv) > 1 else ASSETS.keys()
    
    for name in targets:
        if name not in ASSETS:
            print(f"\n⚠️ 未知素材: {name}")
            continue
            
        config = ASSETS[name]
        print(f"\n🎨 生成: {name}")
        print(f"   比例: {config['aspect_ratio']}")
        
        image_data = generate_image(config['prompt'], config['aspect_ratio'])
        
        if image_data:
            save_image(image_data, config['filename'])
        else:
            print(f"   ❌ 生成失败")
        
        # 避免限流
        time.sleep(2)
    
    print("\n" + "="*60)
    print("✨ 完成！")
    print("="*60)
    
    print("\n📋 使用方式:")
    print("   python generate_logo.py           # 生成全部")
    print("   python generate_logo.py logo      # 只生成 logo")
    print("   python generate_logo.py banner    # 只生成 banner")


if __name__ == "__main__":
    main()
