import httpx, fitz, io, re  # fitz를 사용하기 위해 pymupdf를 설치해야 합니다!

class ParseService:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def filter_references(self, text: str) -> str:
        """
        reference를 제외한 논문 텍스트만을 반환합니다.
        """
        pattern = re.compile(r'\n\s*(references|bibliography)\s*\n', re.IGNORECASE)
        match = pattern.search(text)

        if match:
            return text[:match.start()].strip()
        
        return text.strip()

    async def get_text_by_url(self, pdf_url: str) -> str:
        """
        PDF 내 논문 텍스트를 반환합니다.
        """
        # --- 1. PDF 다운로드 ---
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=30.0) as client:
            response = await client.get(pdf_url)
            pdf_content = response.content  # binary data

        # --- 2. 텍스트 추출 ---
        with fitz.open(stream=io.BytesIO(pdf_content), filetype="pdf") as doc:
            full_text_lst = []
            # 블록 단위 추출: (x0, y0, x1, y1, "text", block_no, block_type)
            for page in doc:
                blocks = page.get_text("blocks")
                # b[6] == 0: 텍스트, b[6] == 1: 이미지
                page_text = "\n".join(b[4] for b in blocks if b[6] == 0)
                full_text_lst.append(page_text)

            full_text = "\n".join(full_text_lst)
            filtered_text = self.filter_references(full_text)
            return filtered_text