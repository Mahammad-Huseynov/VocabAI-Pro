import uvicorn

if __name__ == "__main__":
    # host="0.0.0.0" sistemi lokal şəbəkədəki (Wi-Fi) bütün mobil cihazlara açıq edir.
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
        