import ToolsIotCore


def test_MP70_topic():
    topic = "+/messages/json"
    assert ToolsIotCore.VerifyTopic(topic)
    print(f"Successfully verified topic {topic}")


def test_CMS_topic():
    topic = "GTT/+/SVR/EVP/2100/+/RTRADIO/#"
    assert ToolsIotCore.VerifyTopic(topic)
    print(f"Successfully verified topic {topic}")
