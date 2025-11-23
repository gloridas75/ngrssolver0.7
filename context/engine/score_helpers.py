class ScoreBook:
    """Holds weights and records violations for reporting."""
    def __init__(self, weights):
        self.w = weights
        self.violations = []

    def hard(self, id_, note):
        self.violations.append({"type":"hard","id":id_,"note":note})

    def soft(self, id_, note, penalty):
        self.violations.append({"type":"soft","id":id_,"note":note,"penalty":penalty})
