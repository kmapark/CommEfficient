import json
import os
from collections import defaultdict

import numpy as np

from data_utils import FedDataset, FedCIFAR10
from torchvision.datasets import EMNIST
from PIL import Image

__all__ = ["FedEMNIST"]

# utils methods from Leaf which isn't installable
def read_dir(data_dir):
    clients = []
    groups = []
    data = defaultdict(lambda : None)

    files = os.listdir(data_dir)
    files = [f for f in files if f.endswith('.json')]
    for f in files:
        file_path = os.path.join(data_dir,f)
        with open(file_path, 'r') as inf:
            cdata = json.load(inf)
        clients.extend(cdata['users'])
        if 'hierarchies' in cdata:
            groups.extend(cdata['hierarchies'])
        data.update(cdata['user_data'])

    clients = list(sorted(data.keys()))
    return clients, groups, data


def read_data(train_data_dir, test_data_dir):
    '''parses data in given train and test data directories

    assumes:
    - the data in the input directories are .json files with
        keys 'users' and 'user_data'
    - the set of train set users is the same as the set of test set users

    Return:
        clients: list of client ids
        groups: list of group ids; empty list if none found
        train_data: dictionary of train data
        test_data: dictionary of test data
    '''
    train_clients, train_groups, train_data = read_dir(train_data_dir)
    test_clients, test_groups, test_data = read_dir(test_data_dir)

    assert train_clients == test_clients
    assert train_groups == test_groups

    return train_clients, train_groups, train_data, test_data

class FedEMNIST(FedDataset):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # assume EMNIST is already preprocessed
        # data_dir = '/data/ashwineep/leaf/data/femnist/data/'
        train_data_dir = self.dataset_dir + 'train'
        test_data_dir = self.dataset_dir + 'test'
        self.clients, _, train_data, test_data = read_data(train_data_dir, test_data_dir)
        if self.type == "train":
            self.train_data = train_data
        else:
            self.test_data = test_data
        self.images_per_client = np.array([len(train_data[client_id]['y']) for client_id in self.clients])
        self.val_images_per_client = np.array([len(test_data[client_id]['y']) for client_id in self.clients])

    def _get_train_or_val_item(self, client_id, idx_within_client, train):
        if train:
            dataset = self.train_data
        else:
            dataset = self.test_data
        client = self.clients[client_id]
        client_data = dataset[client]
        x = client_data['x']
        y = client_data['y']
        raw_image = x[idx_within_client]
        raw_image = np.array(raw_image)
        raw_image = np.reshape(raw_image, (28,28))
        target = y[idx_within_client]

        image = Image.fromarray(raw_image)

        return image, target

    def _get_train_item(self, client_id, idx_within_client):
        return self._get_train_or_val_item(client_id, idx_within_client, True)

    def _get_val_item(self, idx):
        cumsum = np.cumsum(self.val_images_per_client)
        client_id = np.searchsorted(cumsum, idx, side="right")
        cumsum = np.hstack([[0], cumsum[:-1]])
        idx_within_client = idx - cumsum[client_id]
        return self._get_val_item_true(client_id, idx_within_client)

    def _get_val_item_true(self, client_id, idx_within_client):
        return self._get_train_or_val_item(client_id, idx_within_client, False)

    def _load_meta(self, train):
        return

    def __len__(self):
        if self.type == "train":
            return 721410
        elif self.type == "val":
            return 81895

    def prepare_datasets(self, download=False):
        return 
        raise RuntimeError("EMNIST should already be here!")

    @property
    def data_per_client(self):
        return self.images_per_client

    @property
    def num_clients(self):
        return len(self.clients)


