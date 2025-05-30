if __name__ == "__main__":
    import os
    import requests

    # Liste der PDF-URLs
    pdf_urls = [
        "https://bvger.weblaw.ch/pdf/A-763-2022_2025-03-31_ff0e850a-347a-4867-9647-2ec871008c42.pdf",
        "https://bvger.weblaw.ch/pdf/A-2720-2023_2024-01-29_13d66c05-1fda-457f-83ab-3010f71d170e.pdf",
        "https://bvger.weblaw.ch/pdf/A-4698-2024_2025-02-25_2da2c290-1620-440a-96b5-b055ac83ddad.pdf",
        "https://bvger.weblaw.ch/pdf/A-4137-2022_2025-04-02_829f7fa0-78a4-494b-a851-b90c1220e6e1.pdf",
        "https://bvger.weblaw.ch/pdf/A-4699-2024_2025-02-25_76a7fe19-7b99-4090-8683-2e9c8ae7b82f.pdf",
        "https://bvger.weblaw.ch/pdf/A-5153-2023_2024-11-11_f0d9086b-6def-4963-b3ec-5ff9beb6ffd0.pdf",
        "https://bvger.weblaw.ch/pdf/A-5060-2023_2025-01-09_2b7a5005-6acf-4ca6-bfd3-dbe90eb06957.pdf",
        "https://bvger.weblaw.ch/pdf/A-1698-2022_2025-03-31_1ae412fb-5157-412f-8d24-067bacf331fa.pdf",
        "https://bvger.weblaw.ch/pdf/A-5680-2023_2024-11-18_51a6d83b-6eb5-4304-8b84-73dc1ffabe52.pdf",
        "https://bvger.weblaw.ch/pdf/A-6208-2023_2025-02-28_d11ec6d4-0fe1-4cea-a1f3-cefaeee44ebf.pdf",
        "https://bvger.weblaw.ch/pdf/A-2360-2023_2024-01-29_f9ec95c7-a592-4b6b-8411-faca733693ee.pdf",
        "https://bvger.weblaw.ch/pdf/A-1504-2023_2024-03-28_f18a9bbe-8e20-4276-a16d-bbfc2bf8698b.pdf",
        "https://bvger.weblaw.ch/pdf/A-4298-2023_2025-02-03_e080f226-7c25-401b-a322-0abbc85e43cc.pdf",
        "https://bvger.weblaw.ch/pdf/A-5059-2023_2025-01-09_232679fa-611f-4f90-a2a2-db461c062405.pdf",
        "https://bvger.weblaw.ch/pdf/A-37-2024_2025-01-08_32882cbb-c3a7-46b6-b0fa-355e318a4625.pdf",
    ]

    # Zielverzeichnis für die heruntergeladenen PDFs
    download_dir = "urteile"
    os.makedirs(download_dir, exist_ok=True)

    # Herunterladen der PDFs
    for url in pdf_urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            filename = os.path.join(download_dir, url.split("/")[-1])
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"Heruntergeladen: {filename}")
        except requests.exceptions.RequestException as e:
            print(f"Fehler beim Herunterladen von {url}: {e}")
