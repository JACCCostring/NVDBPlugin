from PyQt5.QtGui import QStandardItemModel, QStandardItem

class CustomStandardItemModel(QStandardItemModel):
    def __init__(self, parent=None):
        super(CustomStandardItemModel, self).__init__(parent)
        self.data = []
        self.batch_size = 9
        self.fetched_rows = 0


    def feed_data(self, object_data):
        self.clear()
        # Getting the data and then fetching first set of data
        self.data = object_data
        #print(len(self.data[0].keys()), "\n")
        #print(len(self.data[35].keys()), "\n")
        #print(len(self.data[34].keys()), "\n")
        #print(len(self.data[37].keys()), "\n")
        #print(len(self.data[45].keys()), "\n")
        # Setting the headers
        if len(self.data) > 0:
            self.setHorizontalHeaderLabels(self.data[0])
        # setting the first batch of data
        self.fetch_more()


    def fetch_more(self):
        # check if there is data to be fetched
        if self.can_fetch_more():
            # Check the end of the current data_set
            end_index = min(self.fetched_rows + self.batch_size, len(self.data))
            # looping through the data and appending rows
            for i in range(self.fetched_rows, end_index):
                row = []
                # Loop through the keys in the first dictionary (which are used as headers)
                for key in self.data[0].keys():
                    # If the current dictionary has the key, add its value to the row else add empty string
                    if key in self.data[i]:
                        row.append(QStandardItem(str(self.data[i][key])))
                    else:
                        row.append(QStandardItem(''))
                self.appendRow(row)
            self.fetched_rows = end_index
        else:
            print("OUT OF DATA TO FETCH!")


    def can_fetch_more(self):
        # Check if there is data available to be fetched
        return self.fetched_rows < len(self.data)

    def clear_fetch(self):
        self.clear()
        self.fetched_rows = 0


