import unittest
import numpy as np
from FrameRenderer import FrameRenderer

class Test(unittest.TestCase):
    def setUp(self):
        self.testSettings = {
            "resolution": (1920, 1080),
            "bgColor": (0, 0, 0),
            "title": "TEST RENDER",
            "titleColor": (255, 255, 255),
            "artist": "Test Suite",
            "artistColor": (180, 180, 180),
            "primaryColor": (255, 0, 150),
            "secondaryColor": (0, 255, 255),
            "tertiaryColor": (0, 100, 255),
            "borderWidth": 10,
            "borderColor1": (30, 30, 30),
            "borderColor2": (255, 0, 150),
            "barGap": 4,
            "maxHeightPct": 0.5
        }
        self.renderer = FrameRenderer(self.testSettings)

    def testFrameDimensions(self):
        fakeBars = np.full(64, 0.5)
        frame = self.renderer.renderFrame(fakeBars)
        expectedShape = (1080, 1920,  3)
        self.assertEqual(frame.shape, expectedShape)

    def testFrameDataType(self):
        fakeBars = np.zeros(64)
        frame = self.renderer.renderFrame(fakeBars)
        self.assertEqual(frame.dtype, np.uint8)

class TestAudioData(unittest.TestCase):
    def testdataClamping(self):
        rawFreqs = np.array([-0.5, 0.0, 0.5, 1.0, 1.8, 5.0])
        clampedData = np.clip(rawFreqs, 0.0, 1.0)
        self.assertGreaterEqual(np.min(clampedData), 0.0)
        self.assertLessEqual(np.max(clampedData), 1.0)

if __name__ == "__main__":
    unittest.main()