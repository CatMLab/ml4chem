import numpy as np
import torch
from mlchem.utils import get_neighborlist, convert_elapsed_time
from mlchem.data.serialization import dump
from sklearn.externals import joblib
from .cutoff import Cosine
from collections import OrderedDict
import dask
import time
from ase.data import atomic_numbers


class Cartesian(object):
    """Cartesian Coordinates

    Cartesian coordinates are features, too (not very useful ones though). This
    class takes images in ASE format and return them hashed to be used by
    mlchem.


    Parameters
    ----------
    scheduler : str
        The scheduler to be used with the dask backend.
    filename : str
        Name to save on disk of serialized database.
    """
    NAME = 'Cartesian'

    @classmethod
    def name(cls):
        """Returns name of class"""

        return cls.NAME

    def __init__(self, scheduler='distributed', filename='fingerprints.db'):

        self.filename = filename
        self.scheduler = scheduler


    def calculate_features(self, images, purpose='training', data=None,
                           svm=False):
        """Return features per atom in an atoms objects

        Parameters
        ----------
        image : dict
            Hashed images using the DataSet class.
        purpose : str
            The supported purposes are: 'training', 'inference'.
        data : obj
            data object
        svm : bool
            Whether or not these features are going to be used for kernel
            methods.

        Returns
        -------
        feature_space : dict
            A dictionary with key hash and value as a list with the following
            structure: {'hash': [('H', [vector]]}
        """

        print()
        print('Fingerprinting')
        print('==============')

        initial_time = time.time()

        # Verify that we know the unique element symbols
        if data.unique_element_symbols is None:
            print('Getting unique element symbols for {}' .format(purpose))
            unique_element_symbols = \
                data.get_unique_element_symbols(images, purpose=purpose)
            unique_element_symbols = unique_element_symbols[purpose]

            print('Unique elements: {}' .format(unique_element_symbols))


        # We start populating computations with delayed functions to operate
        # with dask's scheduler. These computations get cartesian coordinates.
        computations = []
        for image in images.items():
            key, image = image
            feature_vectors = []
            computations.append(feature_vectors)

            for atom in image:
                index = atom.index
                symbol = atom.symbol

                afp = self.get_atomic_fingerprint(atom, svm=svm)
                feature_vectors.append(afp)

        # In this block we compute the delayed functions in computations.
        feature_space = dask.compute(*computations,
                                     scheduler=self.scheduler)
        hashes = list(images.keys())
        feature_space = OrderedDict(zip(hashes, feature_space))

        fp_time = time.time() - initial_time

        h, m, s = convert_elapsed_time(fp_time)
        print('Fingerprinting finished in {} hours {} minutes {:.2f} '
              'seconds.' .format(h, m, s))

        return feature_space

    @dask.delayed
    def get_atomic_fingerprint(self, atom, svm=False):
        """Delayed class method to compute atomic fingerprints


        Parameters
        ----------
        atom : object
            An ASE atom object.
        svm : bool
            Is this SVM?
        """
        symbol = atom.symbol
        position = atom.position
        if svm is False:
            position = torch.tensor(position, requires_grad=True,
                                    dtype=torch.float)

        return symbol, position

    @dask.delayed
    def restack_image(self, index, image, scaled_feature_space, svm=False):
        """Restack images to correct dictionary's structure to train

        Parameters
        ----------
        index : int
            Index of original hashed image.
        image : obj
            An ASE image object.
        scaled_feature_space : np.array
            A numpy array with the scaled features

        Returns
        -------
        key, features : tuple
            The hashed key image and its corresponding features.
        """
        key, image = image
        features = []
        for j, atom in enumerate(image):
            symbol = atom.symbol
            if svm:
                scaled = scaled_feature_space[index][j]
            else:
                scaled = torch.tensor(scaled_feature_space[index][j],
                                      requires_grad=True,
                                      dtype=torch.float)
            features.append((symbol, scaled))

        return key, features
