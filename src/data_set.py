import numpy as np


class DataSet():
    def __init__(self, data, labels):
        self.data = data
        self._labels = labels

    def split(self, target_col, mask_cols):
        """Split this dataset into rows and labels.

        target_col: the index of the column to use as targetgs
        mask: an iterable of columns indices to hide. The column at
              target_col will be masked whether it appears here or not.
        """
        Y = self.data[:, target_col]
        mask_list = list(mask_cols)
        if target_col not in mask_cols:
            mask_list.append(target_col)

        X = np.copy(data)
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
