"""
===============================================
Load and train Convolutional Neural Network
===============================================

We developed two sequential neural networks to identify the brain MRI contrast.  The first network was a convolutional neural network that inferred the modality on a sagittal slice.  The second network combined the result generated by the first nerwork to infer the modality on the entire volume.  

This script was used to train the convolutional neural network.  The model architecture was loaded from .json string file saved using modality.save_NNarch_toJson.py.  The dataset was previously divided into three sets: training, validation, and testing.  The training set was used to estimate the model parameters.  The validation  set was used to estimate performance after each epoch completed.  The testing set was used in a different script to test the model after training completed. 

The training dataset was too large to load at once so a file_generator was used to generate data as needed by Keras' fit_generator.  The training parameters such as number of epochs, number of steps per epoch, and number of samples per steps were determined emperically and can easily be changed by the user.  The file_generator populates the numpy arrays needed to train the model from randomly selected MRI volumes within the set.  

During the training the weights for the model parameters are saved if performance (accuracy and loss) is improved.  Upon completion this script saves the final weights of the parameters after the number of epochs specified.

"""
print(__doc__)

import numpy as np
import nibabel as nib
import json

np.seterr(all='raise')

from keras.models import model_from_json
from keras.callbacks import ModelCheckpoint, History
from keras.utils import np_utils


def get_files(fn):
    # fn is filename
    with open(fn) as f:
        # files are loaded as tuples with modality and filename
        files = [tuple(i.split(' ')) for i in f]
    return files


def train_CNN(train_files,valid_files,NN,nb_mods,nb_step,input_size):
    # this function loads the neural network architecture, trains
    # the neural network, saves the weights that improve performance,
    # tracks performance (accuracy and loss) 

    # the model was defined and saved in modality.save_NNarch_toJson.py
    model=get_model(NN,nb_mods,verbose=True)
    # syntax to save the weights that improve performance
    checkpath='weights/weights.{epoch:04d}_loss_{loss:0.2f}.h5'
    checkpointer=ModelCheckpoint(checkpath, monitor='loss', verbose=0, save_best_only=True, save_weights_only=True, mode='auto')
    # track performance (accuracy and loss) on train and validation datasets
    performance = History()
    # train the neural network by estimating model parameters that minimize loss
    # determined emperically: nb_step, steps_per_epoch, and epochs
    model.fit_generator(file_generator(train_files, nb_step=nb_step,verbose=False,nb_mods=nb_mods,input_size=input_size), steps_per_epoch=40, epochs=1000, verbose=1,
        validation_data=file_generator(valid_files, nb_step=nb_step,verbose=False,nb_mods=nb_mods,input_size=input_size), validation_steps=1, callbacks=[performance,checkpointer])
    # save the final weights after the training session completes
    model.save_weights('weights/weights.FINAL.h5',overwrite=True)
    # save the performance (accuracy and loss) history
    save_history(performance)


def get_model(NN='CNN',nb_mods=5,verbose=False):
    # load the architecture defined and saved in modality.save_NNarch_toJson.py
    fn = "./model/{0}_{1}mod.json".format(NN,nb_mods)
    # the model architecture is loaded from a .json file 
    with open(fn) as json_data:
        d = json.load(json_data)
    model = model_from_json(d)
    # compile the model architecture to ensure the dimensions match and are correct
    model.compile(loss='categorical_crossentropy',optimizer='nadam',metrics=['accuracy'])
    # print to screen the model architecture, if desired by user
    if verbose:
        print(model.summary())
    return model


def save_history(performance):
    # track performance (accuracy and loss) for training and validation sets
    # after each epoch completes and save as .json string
    json_string=json.dumps(performance.history)
    fn='history_parms.json'
    with open(fn, 'w') as outfile:
        json.dump(json_string, outfile)


def file_generator(files,nb_step=100,verbose=False,nb_mods=8,input_size=(1,32,32)):
    # this function is called while training by Keras' fit_generator function
    # it generates the data for both the training and validation sets

    # set a warning level in case there are NaN in the data
    np.seterr(all='raise')
    # X contains nb_step sagittal slices extracted from random MRI volumes
    X = np.zeros((nb_step,) + input_size )
    # Y contains nb_step true modalities from same MRI volumes in X
    Y = np.zeros((nb_step, nb_mods))
    # infinite loop needed to continue generating data whle training
    while True:
        # n is the slice number looping over
        n = 0
        # populate X and Y until the required nb_step is reached
        while n < nb_step:
            # number of slices to extract from each MRI volume
            nb_slices = 30
            # inserted try and except to catch problematic volumes
            try:
                # randomly select one volume from the list of files
                idx = np.random.randint(0, len(files))
                # modality categorized as a number and read from file
                mod = int(files[idx][0])
                # filename read from files
                f = files[idx][1].strip()
                # ensure the read mod is within the nb_mods maximum value
                if mod < nb_mods:
                    # if desired print to screen the modality and filename
                    if verbose:
                        print("{} : {}".format(mod, f))
                    # load file as a numpy array using nibabel
                    img = nib.load(f).get_data()
                    # reorder and invert axes
                    img = np.swapaxes(img,0,2)
                    img = img[::-1, ::-1, :]

                    # in case the volume does not have enough sagittal slices
                    if nb_slices>img.shape[0]:
                        nb_slices=img.shape[0]
                    # get nb_slices sagittal slices from img as numpy array
                    try:
                        data = get_img_data(img,nb_slices)
                    except Exception as e:
                        print("Warning: {} {}".format(e, f))
                        continue
                    # catch for NaN values in the MRI volume
                    if not np.all(np.isfinite(data)):
                        print("Loaded NaN values with {}".format(f)) 
                        continue

                    # update nb_slices, if needed
                    nb_slices=data.shape[0]
                    # calculate how many slices are needed to continue populating 
                    need_slices=nb_step-n
                    # in this case we only need need_slices
                    if need_slices < nb_slices:
                        # populate X and Y with data and modality as category
                        X[n:n+need_slices,:,:,:] = data[:need_slices,:,:,:]
                        Y[n:n+need_slices,:] = np_utils.to_categorical([mod]*need_slices, nb_mods)
                    # in this case we need all nb_slices
                    else:
                        # populate X and Y with data and modality as category
                        X[n:n+nb_slices,:,:,:] = data
                        Y[n:n+nb_slices,:] = np_utils.to_categorical([mod]*nb_slices, nb_mods)
                    # increase n by nb_slices used
                    n += nb_slices
            # catch error and print
            except Exception, e:
                print(str(e))
                pass
        # yield X,Y to fit_generator()
        yield X,Y


def get_img_data(img,nb_slices=30):
    # Get image data and normalize
    img = np.array(img).astype('float32')
    img = grab_sagittal(img,nb_slices)
    img = reshape_dimension(img)
    return img


def grab_sagittal(img,nb_slices):
    # extract sagittal nb_slices from img and preprocess
    # total number of sagittal slices in the MRI volume
    x_total = img.shape[0]
    # middle of the volume in the sagittal direction
    x_mid = np.around(x_total / 2).astype(int)
    # sagittal_volume is a list to populate in for loop and returned as numpy array
    sagittal_volume=[]
    # window is nb_slices divided by 2
    window = np.round(nb_slices / 2).astype(int)  
    for x_idx in range(x_mid-window,x_mid+window):
        # sagittal slice extraced from img
        slice_sagittal=img[x_idx,:,:]
        # resample the sagittal slice to 32x32
        slice_resampled=resample_slice(slice_sagittal)
        # intensity normalize each slice
        slice_normalized=normalize(slice_resampled)
        # append to volume slice by slice
        sagittal_volume.append(slice_normalized)
    # return as a numpy array
    return np.asarray(sagittal_volume)


def resample_slice(dSlice):
    # size of the slice
    (Ny,Nz)=dSlice.shape
    # resample each slice to make it 32x32
    s=np.linspace(0,31,32)/32
    # sample in the y-direction
    sy=np.around(s*Ny).astype(int)
    tmp=dSlice[sy,:]
    # sample in the z-direction
    sz=np.around(s*Nz).astype(int)
    return tmp[:,sz]


def normalize(slice_array):
    # slice_array is intensity normalized by mean and variance
    # mean of the slice
    m=np.mean(slice_array)
    # standard deviation of the slice_array
    st=np.std(slice_array)
    slice_normalized = (slice_array - m) / st
    return slice_normalized


def reshape_dimension(img):
    # reorder the dimensions for the neural network architecture
    (x,y,z)=img.shape
    return np.reshape(img,(x,1,y,z))


# the entire dataset was split into three groups:
# train: list of files used for training the algorithm
# valid: list of files used for validation after each training epoch
# test : list of files used for testing the algorithm after training

# this code uses the files located in training and validation groups

train_fn = './cross_valid_fns/train.filenames.txt'
valid_fn = './cross_valid_fns/valid.filenames.txt'

train_files=get_files(train_fn)
valid_files=get_files(valid_fn)

# select the convolution neural network (CNN)
NN='CNN'
# number of modalities: [5,8] can be altered
nb_mods=5 
# number of sagittal slices used by the neural network
# while taking a training step and validation step
nb_step=100
# the dimension of one sagittal slice
input_size=(1,32,32)
# the size for the training dataset
train_size=len(train_files)
# print to the screen information regarding the training session
print('\n==Training {0}, number of modalities:{1}, dataset size:{2}==\n'.format(NN,nb_mods,train_size))
# execute training command
train_CNN(train_files,valid_files,NN,nb_mods,nb_step,input_size)


