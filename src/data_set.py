import numpy as np
from sklearn.preprocessing import scale


class DataSet:
    def __init__(self, data, labels):
        self.data = data
        self._labels = labels
        self._mask_list = []

    def split(self, target_col, mask_cols=None):
        """Split this dataset into rows and labels.

        target_col: the index of the column to use as targetgs
        mask: an iterable of columns indices to hide. The column at
              target_col will be masked whether it appears here or not.
        """
        if mask_cols is None:
            mask_cols = list()

        Y = self.data[:, target_col]
        mask_list = list(set(mask_cols).union(self._mask_list))
        if target_col not in mask_cols:
            mask_list.append(target_col)

        X = np.copy(self.data)
        X[:, mask_list] = 0

        return DataSplit(self.data, self.labels, X, Y, mask_list)

    @property
    def labels(self):
        return self._labels


class DataSplit(DataSet):
    def __init__(self, data, labels, X, Y, mask_list):
        super().__init__(data, labels)
        self.X = X
        self.Y = Y
        self._mask_list = mask_list

    @property
    def labels(self):
        hidden_labels = []
        for i, label in enumerate(self._labels):
            if i in self._mask_list:
                hidden_labels.append("H_" + label)
            else:
                hidden_labels.append(label)
        return hidden_labels

    def unmask(self, col_id):
        if col_id not in self._mask_list:
            raise Exception(f"col {col_id} is not masked")
        self._mask_list.remove(col_id)
        self.X[:, col_id] = self.data[:, col_id]
        return self

    def reset(self):
        """Return a Dataset with nothing masked"""
        return DataSet(self.data, self.labels)

    def scale(self):
        self.X = scale(self.X)
        return self
