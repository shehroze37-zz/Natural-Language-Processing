class Fold:

    fileNames = []
    startLine = ""
    endLine = ""
    iden = -1
    sentences = []

    def __init__(self, iden):
        self.fileNames = [] 
        self.sentences = []
        self.iden = iden 

    def addFileName(self,filename ):
        self.fileNames.append(filename)          