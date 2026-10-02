import google.generativeai as genai
import PIL.Image
import requests
from io import BytesIO
import json

# ตั้งค่า Gemini API Key
genai.configure(api_key="YOUR_GEMINI_API_KEY")

def analyze_cctv_image(image_url):
    # 1. ดึงภาพจาก URL กล้อง CCTV
    response = requests.get(image_url)
    img = PIL.Image.open(BytesIO(response.content))

    # 2. เรียกใช้โมเดล Gemini
    model = genai.GenerativeModel('gemini-2.5-flash')

    # 3. กำหนด Prompt บังคับให้ตอบกลับเป็น JSON เท่านั้น
    prompt = """
    วิเคราะห์ภาพจากกล้องวงจรปิดจราจรนี้อย่างละเอียด แล้วประเมินสถานะน้ำท่วมขังบนผิวจราจร
    ตอบกลับเฉพาะรูปแบบ JSON ดังนี้เท่านั้น ห้ามใส่ข้อความอื่นนอกเหนือจาก JSON:
    {
        "is_flooded": boolean (true ถ้าพบน้ำท่วมขังบนถนน, false ถ้าไม่มี),
        "confidence": float (0.0 ถึง 1.0),
        "severity": "ไม่มี" | "เล็กน้อย" | "ปานกลาง" | "สูง",
        "description": "คำอธิบายสั้นๆ ภาษาไทยเกี่ยวกับสภาพถนนในภาพ"
    }
    """

    # 4. ส่งภาพและ Prompt ให้ Gemini ประมวลผล
    result = model.generate_content([prompt, img])
    
    # แปลงผลลัพธ์เป็น JSON Object
    try:
        data = json.loads(result.text.strip().replace('```json', '').replace('```', ''))
        return data
    except Exception as e:
        print("Error parsing JSON:", e)
        return None

# ตัวอย่างการใช้งาน
if __name__ == "__main__":
    cctv_test_url = "https://example.com/path-to-cctv-snapshot.jpg"
    # analysis_result = analyze_cctv_image(cctv_test_url)
    # print(analysis_result)