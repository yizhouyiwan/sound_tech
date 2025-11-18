# test_translation.py
import requests
import json

# 测试翻译API
def test_translation(text,style='json'):
    url = "http://localhost:8000/api/v1/translate"
    
    # 测试数据
    test_data = {
        "text": text,
        "output_format": style,  # 测试Word导出
        "include_vocabulary": True
    }
    
    try:
        response = requests.post(url, json=test_data)
        result = response.json()
        
        print("API响应:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get("success") and "word_document_url" in result:
            # 下载Word文档
            doc_url = f"http://localhost:8000{result['word_document_url']}"
            doc_response = requests.get(doc_url)
            
            if doc_response.status_code == 200:
                with open("test_translation.docx", "wb") as f:
                    f.write(doc_response.content)
                print("Word文档已保存: test_translation.docx")
            
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    while True:
        text = input("请输入要翻译的文本（输入'exit'退出）：")
        style = input("需要Word文档或json输出（输入'word or json'）：")
        style = 'word' if style.lower() == 'word' else 'json' 
        if text.lower() == 'exit':
            break
        test_translation(text=text,style=style)
    