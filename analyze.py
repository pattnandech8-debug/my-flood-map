import json
import time
from io import BytesIO
import requests
from google import genai
from PIL import Image

# ==================== ตั้งค่า API KEYS ====================
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"  # นำ API Key จาก Google AI Studio มาใส่ที่นี่
LONGDO_API_KEY = "8df7c58d93c1a2fdcaee05f9fe3e2b93"

# ตั้งค่า Client สำหรับ Gemini SDK ใหม่ (google-genai)
client = genai.Client(api_key=GEMINI_API_KEY)

# คำสั่งบังคับให้ Gemini อ่านภาพสภาพน้ำท่วมแล้วตอบเป็น JSON เท่านั้น
PROMPT = """
วิเคราะห์ภาพจากกล้องวงจรปิดจราจรนี้อย่างละเอียด แล้วประเมินสภาพน้ำท่วมขังบนผิวจราจร
ตอบกลับเฉพาะรูปแบบ JSON ดังนี้เท่านั้น ห้ามใส่ข้อความ Markdown หรือคำอธิบายเพิ่มนอกเหนือจาก JSON:
{
    "is_flooded": true หรือ false,
    "severity": "ไม่มี" หรือ "เล็กน้อย" หรือ "ปานกลาง" หรือ "สูง",
    "description": "อธิบายสภาพถนนและระดับน้ำขังภาษาไทยสั้นๆ 1 ประโยค"
}
"""


def fetch_longdo_cameras():
    """ดึงข้อมูลจุดกล้องและ URL รูปภาพทั้งหมดจาก Longdo Traffic API"""
    url = f"https://api.longdo.com/traffic/json/cameras?key={LONGDO_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"❌ ดึงข้อมูลกล้อง Longdo ล้มเหลว: {e}")
    return []


def analyze_cctv_image(image_url):
    """โหลดภาพจาก URL กล้องแล้วส่งให้ Gemini 2.5 Flash ประมวลผล"""
    try:
        res = requests.get(image_url, timeout=10)
        img = Image.open(BytesIO(res.content))

        # เรียกใช้งาน Gemini 2.5 Flash (โมเดลประมวลผลภาพรวดเร็วและประหยัด)
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=[PROMPT, img]
        )

        # ทำความสะอาดผลลัพธ์ JSON
        cleaned_text = (
            response.text.strip()
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"⚠️ เกิดข้อผิดพลาดในการวิเคราะห์ภาพ {image_url}: {e}")
        return {
            "is_flooded": False,
            "severity": "ไม่ระบุ",
            "description": "ไม่สามารถดึงภาพหรือวิเคราะห์ได้",
        }


def main():
    cameras = fetch_longdo_cameras()
    print(f"📷 พบกล้องจาก Longdo API ทั้งหมด {len(cameras)} จุด")

    results = []

    # เพื่อประหยัดเวลาและ API Quota ขอแนะนำให้ทดสอบรัน 10-20 จุดแรกก่อน (หรือลบ [:15] ออกหากต้องการรันทั้งหมด)
    target_cameras = cameras[:15]

    for index, cam in enumerate(target_cameras, start=1):
        cam_id = cam.get("id")
        title = cam.get("title") or cam.get("name") or f"กล้อง CCTV {index}"
        lat = cam.get("lat")
        lng = cam.get("long") or cam.get("lng")
        img_url = cam.get("url") or cam.get("image")

        if not img_url or not lat or not lng:
            continue

        print(f"[{index}/{len(target_cameras)}] กำลังวิเคราะห์จุด: {title}...")

        # ส่งภาพวิเคราะห์ด้วย Gemini
        ai_result = analyze_cctv_image(img_url)

        # บันทึกข้อมูล
        results.append(
            {
                "id": str(cam_id),
                "name": title,
                "lat": float(lat),
                "lng": float(lng),
                "baseUrl": img_url,
                "isFlooded": ai_result.get("is_flooded", False),
                "severity": ai_result.get("severity", "ไม่มี"),
                "waterLevel": ai_result.get("description", "สภาพการจราจรปกติ"),
                "updatedAt": time.strftime("%H:%M น."),
            }
        )

        # หน่วงเวลา 1.5 วินาที เพื่อไม่ให้เกิน Rate Limit ของ Free Quota
        time.sleep(1.5)

    # บันทึกเป็นไฟล์ flood_data.json สำหรับหน้าเว็บ
    with open("flood_data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(
        "\n✅ วิเคราะห์เรียบร้อย! สร้างไฟล์ flood_data.json สำเร็จพร้อมนำไปใช้บนหน้าเว็บ"
    )


if __name__ == "__main__":
    main()