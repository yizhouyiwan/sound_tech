import requests
import json
import unittest

BASE_URL = "http://localhost:5000"

class TestVideoConferenceAPI(unittest.TestCase):
    
    def test_1_create_room(self):
        """测试创建房间"""
        response = requests.post(f"{BASE_URL}/api/v1/rooms", json={
            "room_name": "test_room",
            "user_id": 123456
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('room_id', data)
        self.assertIn('token', data)
        
        print("✅ 创建房间测试通过")
        return data['room_id']
    
    def test_2_join_room(self, room_id):
        """测试加入房间"""
        response = requests.post(f"{BASE_URL}/api/v1/rooms/{room_id}/join", json={
            "user_id": 654321
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('token', data)
        
        print("✅ 加入房间测试通过")
    
    def test_3_start_recording(self, room_id):
        """测试开始录制"""
        response = requests.post(f"{BASE_URL}/api/v1/rooms/{room_id}/record/start")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('recording_id', data)
        
        print("✅ 开始录制测试通过")
        return data['recording_id']
    
    def test_4_stop_recording(self, room_id, recording_id):
        """测试停止录制"""
        response = requests.post(f"{BASE_URL}/api/v1/rooms/{room_id}/record/stop", json={
            "recording_id": recording_id
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        print("✅ 停止录制测试通过")
    
    def test_5_get_recording(self, recording_id):
        """测试获取录制信息"""
        response = requests.get(f"{BASE_URL}/api/v1/recordings/{recording_id}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('recording', data)
        
        print("✅ 获取录制信息测试通过")

def run_tests():
    """运行所有测试"""
    tester = TestVideoConferenceAPI()
    
    try:
        # 测试创建房间
        room_id = tester.test_1_create_room()
        
        # 测试加入房间
        tester.test_2_join_room(room_id)
        
        # 测试录制功能
        recording_id = tester.test_3_start_recording(room_id)
        tester.test_4_stop_recording(room_id, recording_id)
        tester.test_5_get_recording(recording_id)
        
        print("\n🎉 所有测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")

if __name__ == "__main__":
    run_tests()