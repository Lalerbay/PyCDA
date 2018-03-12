import numpy as np
import pkg_resources

class DetectorBaseClass(object):
    """This is the base class for a detector object.
    Attributes in the __init__ method should be specified 
    by child detectors.
    """
    def __init__(self):
        """Detectors must specify these attributes."""
        #Specify the dimensions of input image (x, y)
        self.input_dims = (0, 0)
        #Three channels if RGB image; 1 if greyscale
        self.input_channels = 3
        #dimensions of prediction (x, y)
        self.output_dims = (0, 0)
        #set to "center" if the output pixels map directly to input
        self.in_out_map = None
        #Recommended batch size should be do-able for modest machines
        self.rec_batch_size = 1
        #Set to "pixel-wise" if detector makes per-pixel prediction
        self.prediction_type = None
        
    def predict(self, batch):
        """Predict method takes a batch and returns a batch of predictions.
        Output should be a batch of single-channel images of shape:
        (batch_size, self.output_dims[0], self.output_dims[1], 1)
        """
        raise Exception('Error: the detector base class cannot make predictions.')
        
class DummyDetector(DetectorBaseClass):
    """The dummy detector is used for testing. It returns predictions
    when called; the predictions contain random values between 0 and 1,
    in the dimensions specified at initialization.
    """
    def __init__(self, input_dims=(256, 256), output_dims=(172, 172), n_channels=1, batch_size=5):
        self.input_dims = input_dims
        self.input_channels = n_channels
        self.output_dims = output_dims
        self.in_out_map = 'center'
        self.rec_batch_size = batch_size
        self.prediction_type = 'pixel-wise'
        
    def predict(self, batch):
        """returns a batch of random-pixel images with appropriate shape."""
        try:
            assert (batch.shape[2], batch.shape[1]) == self.input_dims
        except AssertionError:
            raise Exception('input image shape must match detector.input_dims')
        batch_size = batch.shape[0]
        predictions = []
        for i in range(batch_size):
            prediction = np.random.rand(self.output_dims[0], self.output_dims[1])
            prediction = np.expand_dims(prediction, axis=-1)
            predictions.append(prediction)
        return np.array(predictions)
    
class UnetDetector(DetectorBaseClass):
    """U-net convolutional model to generate pixel-wise
    prediction. Its output is a per-pixel likelihood that
    a given pixel is a part of a crater surface feature.
    Single color channel (grayscale).
    """
    def __init__(self):
        import tensorflow as tf
        from keras.models import load_model
        self.input_dims = (256, 256)
        #one color channel; greyscale
        self.input_channels = 1
        self.output_dims = (172, 172)
        self.in_out_map = 'center'
        #small batches due to high memory requirements.
        self.rec_batch_size = 3
        self.prediction_type = 'pixel-wise'
        path = pkg_resources.resource_filename('pycda', 'models/unet_light_model.h5')
        self.model = load_model(path)
        
    def predict(self, batch):
        """returns a batch of random-pixel images with appropriate shape."""
        return self.model.predict(batch)
        
class TinyDetector(DetectorBaseClass):
    """A tiny version of U-Net downsized for speed. 
    Its output is a per-pixel likelihood that
    a given pixel is a part of a crater surface feature.
    Single color channel (grayscale).
    """
    def __init__(self):
        import tensorflow as tf
        from keras.models import load_model
        self.input_dims = (256, 256)
        #one color channel; greyscale
        self.input_channels = 1
        self.output_dims = (172, 172)
        self.in_out_map = 'center'
        #small batches due to high memory requirements.
        self.rec_batch_size = 12
        self.prediction_type = 'pixel-wise'
        path = pkg_resources.resource_filename('pycda', 'models/tinynet.h5')
        self.model = load_model(path)
        
    def predict(self, batch):
        """returns a batch of random-pixel images with appropriate shape."""
        return self.model.predict(batch)

        
def get(identifier):
    """handles argument to CDA pipeline for detector specification.
    returns an initialized detector.
    """
    model_dictionary = {
        'dummy': DummyDetector,
        'unet': UnetDetector
    }
    if identifier is None:
        raise Exception('You must specify a detector model.')
    if isinstance(identifier, DetectorBaseClass):
        model = identifier
        return model
    elif identifier in model_dictionary:
        return model_dictionary[identifier]()
    elif callable(identifier):
        if isinstance(identifier(), DetectorBaseClass):
            return identifier()
        else:
            raise Exception('custom detectors must inherit'
                           'from DetectorBaseClass, which can be'
                           'imported from detectors.py')
    else:
        raise ValueError('Could not interpret '
                         'detection model identifier: {} \n'
                         'try one of these keywords: {}'
                         .format(identifier, list(model_dictionary.keys())))
        
        
        
