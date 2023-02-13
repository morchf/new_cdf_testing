import ToolsIotCore

def test_MP70_topic():
    topic = "+/messages/json"
    assert ToolsIotCore.VerifyTopic(topic)
    print(f"Successfully verified topic {topic}")

def test_RTRADIO_topic():
    topic = "GTT/+/VEH/EVP/2100/+/RTRADIO"
    assert ToolsIotCore.VerifyTopic(topic)
    print(f"Successfully verified topic {topic}")

def test_CMS_topic():
    topic = "GTT/+/ALL/EVP/2100/+/RTRADIO/#"
    assert ToolsIotCore.VerifyTopic(topic)
    print(f"Successfully verified topic {topic}")