from a2a.types import AgentCard
from message.code import Code

class ModelManager:
    def __init__(self):
        self.models = {}

    def register_model(self, model_name: str, information : AgentCard) :
        if model_name not in self.models:
            self.models[model_name] = information
            coder = Code(200, '注册成功')
            return coder.json()
        else:
            coder = Code(400, '模型已存在')
            return coder.json()

    def get_model(self, model_name: str) -> AgentCard:
        if model_name in self.models:
            return self.models[model_name]
        else:
            raise ValueError(f'Model {model_name} not found')

    def list_models(self):
        return list(self.models.keys())