from enum import IntEnum
from ModelBase import ModelBase
from SharedContext import db



class MessagePacket(IntEnum):
    MCQ_ID = 0
    QUESTION = 1
    OPTION_1 = 2
    OPTION_2 = 3
    OPTION_3 = 4
    OPTION_4 = 5
    OPTION_1_VOTE = 6
    OPTION_2_VOTE = 7
    OPTION_3_VOTE = 8
    OPTION_4_VOTE = 9
    ROOM = 10


class MCQModel(db.Model):
    __bind_key__ = "mcq"

    mcq_id = db.Column(db.String(120), unique=True, nullable=False, primary_key=True)
    question = db.Column(db.String(120), unique=False, nullable=False, primary_key=False)
    option_1 = db.Column(db.String(120), unique=False, nullable=False, primary_key=False)
    option_2 = db.Column(db.String(120), unique=False, nullable=False, primary_key=False)
    option_3 = db.Column(db.String(120), unique=False, nullable=False, primary_key=False)
    option_4 = db.Column(db.String(120), unique=False, nullable=False, primary_key=False)
    option_1_vote = db.Column(db.Integer, unique=False, nullable=False, primary_key=False)
    option_2_vote = db.Column(db.Integer, unique=False, nullable=False, primary_key=False)
    option_3_vote = db.Column(db.Integer, unique=False, nullable=False, primary_key=False)
    option_4_vote = db.Column(db.Integer, unique=False, nullable=False, primary_key=False)
    room = db.Column(db.String(120), unique=False, nullable=False, primary_key=False)

    def __repr__(self):
        return 'MCQ {} {} {} {} {} {} {} {} {} {} {}'.format(self.mcq_id, self.question, self.option_1, self.option_2, self.option_3, self.option_4, self.option_1_vote, self.option_2_vote, self.option_3_vote, self.option_4_vote, self.room) 
    def __init__(self, **kwargs):
        super(MCQModel, self).__init__(**kwargs)

    def SaveDatabase(filePath):
        # pull all clients.
        ModelBase.ProcessDatabase(MCQModel.query.all(), filePath)
        print("SAVED MCQ DB TO {}".format(filePath))









