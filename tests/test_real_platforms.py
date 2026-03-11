import pytest
import requests
import os


class TestRealPlatforms:
    @pytest.mark.integration
    def test_pollinations_real_api(self):
        url = "https://image.pollinations.ai/prompt/test"
        params = {"width": 256, "height": 256, "nologo": "true"}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 502:
                pytest.skip("pollinations 服务暂时不可用 (502)")
            if response.status_code == 503:
                pytest.skip("pollinations 服务暂时不可用 (503)")
            assert response.status_code == 200, f"状态码: {response.status_code}"
            assert len(response.content) > 1000, "图片数据太小"
            assert response.headers.get("Content-Type", "").startswith("image"), "不是图片响应"
            print(f"✅ pollinations 可用，图片大小: {len(response.content)} bytes")
        except requests.exceptions.Timeout:
            pytest.skip("pollinations 服务超时")
        except requests.exceptions.ConnectionError:
            pytest.skip("pollinations 服务连接失败")

    @pytest.mark.integration
    def test_pollinations_turbo_real_api(self):
        url = "https://image.pollinations.ai/prompt/test"
        params = {"width": 256, "height": 256, "nologo": "true", "model": "turbo"}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code in [502, 503]:
                pytest.skip(f"pollinations-turbo 服务暂时不可用 ({response.status_code})")
            assert response.status_code == 200, f"状态码: {response.status_code}"
            assert len(response.content) > 1000, "图片数据太小"
            print(f"✅ pollinations-turbo 可用，图片大小: {len(response.content)} bytes")
        except requests.exceptions.Timeout:
            pytest.skip("pollinations-turbo 服务超时")
        except requests.exceptions.ConnectionError:
            pytest.skip("pollinations-turbo 服务连接失败")

    @pytest.mark.integration
    def test_pollinations_flux_real_api(self):
        url = "https://image.pollinations.ai/prompt/test"
        params = {"width": 256, "height": 256, "nologo": "true", "model": "flux"}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code in [502, 503]:
                pytest.skip(f"pollinations-flux 服务暂时不可用 ({response.status_code})")
            assert response.status_code == 200, f"状态码: {response.status_code}"
            assert len(response.content) > 1000, "图片数据太小"
            print(f"✅ pollinations-flux 可用，图片大小: {len(response.content)} bytes")
        except requests.exceptions.Timeout:
            pytest.skip("pollinations-flux 服务超时")
        except requests.exceptions.ConnectionError:
            pytest.skip("pollinations-flux 服务连接失败")


class TestZhipuCogView:
    @pytest.mark.integration
    def test_zhipu_cogview_api(self):
        api_key = os.getenv("GLM_API_KEY")
        if not api_key or api_key == "your_glm_api_key_here":
            pytest.skip("未配置 GLM_API_KEY 环境变量")
        
        url = "https://open.bigmodel.cn/api/paas/v4/images/generations"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": "cogview-3",
            "prompt": "一只可爱的猫"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            if response.status_code == 401:
                pytest.skip("GLM API Key 无效或已过期")
            if response.status_code == 429:
                pytest.skip("GLM API 调用频率超限")
            assert response.status_code == 200, f"状态码: {response.status_code}, 响应: {response.text[:200]}"
            
            data = response.json()
            assert "data" in data, f"响应格式错误: {data}"
            assert len(data["data"]) > 0, "没有返回图片"
            assert "url" in data["data"][0], "响应中没有图片URL"
            
            image_url = data["data"][0]["url"]
            print(f"✅ 智谱AI CogView 可用，图片URL: {image_url}")
            
            img_response = requests.get(image_url, timeout=30)
            assert img_response.status_code == 200, "无法下载图片"
            assert len(img_response.content) > 1000, "图片数据太小"
            print(f"✅ 图片下载成功，大小: {len(img_response.content)} bytes")
            
        except requests.exceptions.Timeout:
            pytest.skip("智谱AI 服务超时")
        except requests.exceptions.ConnectionError:
            pytest.skip("智谱AI 服务连接失败")

    @pytest.mark.integration
    def test_zhipu_cogview_chinese_prompt(self):
        api_key = os.getenv("GLM_API_KEY")
        if not api_key or api_key == "your_glm_api_key_here":
            pytest.skip("未配置 GLM_API_KEY 环境变量")
        
        url = "https://open.bigmodel.cn/api/paas/v4/images/generations"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": "cogview-3",
            "prompt": "水墨画风格的山水，远山近水，云雾缭绕"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            if response.status_code in [401, 429]:
                pytest.skip(f"API 调用受限 ({response.status_code})")
            assert response.status_code == 200, f"状态码: {response.status_code}"
            
            data = response.json()
            assert "data" in data and len(data["data"]) > 0
            print(f"✅ 中文提示词测试通过")
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"网络错误: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
