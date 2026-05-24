from web import app
import uvicorn

if __name__ == "__main__":
    print("="*60)
    print("🔥 截教对战服务器启动成功")
    print("👉 访问 http://127.0.0.1:8000")
    print("="*60)
    uvicorn.run(app, host="0.0.0.0", port=8000)