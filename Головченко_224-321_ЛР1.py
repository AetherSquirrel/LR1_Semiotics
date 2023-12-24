import json


def json_load(file):
    with open(file, 'r') as f:
        return json.load(f)


def tolist(x, dtype=int):
    if isinstance(x, (int, float)):
        return [x]
    elif isinstance(x, str):
        return [dtype(i) for i in x.replace(' ', '').split(',')]
    else:
        return list(x)


class System:
    def __init__(self):
        qu = json_load('questions.json')
        qu = {int(k): v for k, v in qu.items()}
        ob = json_load('TV.json')
        ruls = json_load('rules.json')

        for i in qu.values():
            if 'parameter' in i:
                i['attribute'] = i['parameter']
        for i in ruls.values():
            if 'parameters' in i:
                i['attributes'] = i['parameters']

        self.qu = qu
        self.ob = ob
        self.ru = ruls
        self.qu_rem = set([1])
        self.qu_ex = set([])
        self.ob_match = self.ob.copy()
        self.attrs = {}
        self.qu_cur = 1

    def question(self, qu_id=None):
        if qu_id is None: qu_id = self.qu_cur
        assert qu_id in self.qu, f'ERROR! Question {qu_id} does not exist.'
        assert qu_id not in self.qu_ex, f'ERROR! Question {qu_id} already used!'

        qu = self.qu[qu_id]
        self.qu_ex.add(qu_id)

        attr = qu['attribute'] if 'attribute' in qu else None

        print(f"Вопрос #{qu_id}: {qu['question']}")

        if 'choose' in qu['type']:
            for x, y in enumerate(
                    qu['answers'].keys() if isinstance(qu['answers'], dict)
                    else qu['answers']):
                print(f'{x + 1}:{y}')

            ans = False
            while type(ans) == bool:
                try:
                    ans = tolist(input('Введите ответы через пробел: ' if 'multi_choose' in qu['type']
                                       else 'Введите ответ: '))
                except:
                    print('Ошибка, попробуйте снова.')

            if ans != 0:
                for x, y in enumerate(
                        qu['answers'].items() if isinstance(qu['answers'], dict)
                        else qu['answers']):
                    if x + 1 in ans:

                        if attr:
                            if attr not in self.attrs: self.attrs[attr] = set()
                            self.attrs[attr].add(y[0] if isinstance(y, tuple) else y)
                        if isinstance(y, tuple):
                            for attr, value in y[1].items():
                                if attr not in self.attrs: self.attrs[attr] = set()
                                if isinstance(value, list):
                                    self.attrs[attr].update(set(value))
                                else:
                                    self.attrs[attr].add(value)


        elif qu['type'] == 'yes/no':
            assert attr, f'ERROR! "Yes/No" question should have "attribute" or "parameter" field!'
            print('1. Да \n2. Нет')
            ans = False
            while True:
                try:
                    ans = int(input('Введите ответ: '))
                    if ans == 1:
                        self.attrs[attr] = {True}
                        break
                    elif ans == 2:
                        self.attrs[attr] = {False}
                        break
                    else:
                        raise ValueError()
                except:
                    print('Ошибка, попробуйте снова.')

        elif 'input' in qu['type']:
            assert attr, f'ERROR! "Input" question should have "attribute" or "parameter" field!'
            ans = False
            while type(ans) == bool:
                try:
                    ans = int(input('Введите ответ: '))
                except:
                    print('Ошибка, попробуйте снова.')
            if ans != 0:
                if attr not in self.attrs: self.attrs[attr] = set()
                self.attrs[attr].add(f'COND {ans} -')

        self.chk_ruls()
        if 'next question' in qu:
            if qu['next question'] not in self.qu_ex:
                self.qu_cur = qu['next question']
            else:
                self.qu_cur = list(self.qu_rem)[0] if len(self.qu_rem) > 0 else None
        else:
            self.qu_cur = list(self.qu_rem)[0] if len(self.qu_rem) > 0 else None
        return self.qu_cur

    def chk_ruls(self):
        for x in self.ru.keys(): self.chk_rul(x)
        for x in self.qu_rem.copy():
            if x in self.qu_ex: self.qu_rem.remove(x)

    def chk_rul(self, rulid):
        assert rulid in self.ru, f'ERROR! There is no rule {rulid}.'
        rule = self.ru[rulid]

        match = True
        for x, y in rule['attributes'].items():
            if not self.condt(x, y):
                match = False
                break

        if match:
            if 'enable' in rule: self.qu_rem.update(tolist(rule['enable']))
            if 'skip' in rule: self.qu_ex.update(tolist(rule['skip']))

        return match

    def condt(self, att, con):
        if att not in self.attrs: return False
        if isinstance(con, str) and con.startswith('COND '):
            return self.attrs[att] <= float(con[8:-1])
        elif isinstance(con, list):
            for x in con:
                if x in self.attrs[att]: return True
            return False
        else:
            return con in self.attrs[att]

    def chk_ob(self, ob_id):
        assert ob_id in self.ob, f'Объект {ob_id} не существует'
        obj = self.ob[ob_id]
        matches = True
        for oa, ov in obj.items():

            # Проверяется атрибут объекта
            if oa in self.attrs:
                for condition in self.attrs[oa]:
                    if isinstance(condition, str) and condition.startswith('COND '):
                        if condition.endswith('+'):
                            if ov < float(condition[5:-1]): matches = False
                        if condition.endswith('-'):
                            if ov > float(condition[5:-1]): matches = False
                    else:
                        if (ov is False and ov not in self.attrs[oa]) or (
                                (not isinstance(ov, bool)) and ov not in self.attrs[oa]): matches = False
                    if matches is False: return matches
        return matches

    def chk_objs(self):
        match_obj = []
        for x in self.ob.keys():
            if self.chk_ob(x): match_obj.append(x)
        return match_obj

    def exec(self):
        while True:
            if not self.question(): break
        match = self.chk_objs()
        print()
        if len(match) > 0:
            n = '\n'
            print(f'Вам подходят эти телевизоры: {n}{n.join(match)}')
        else:
            print(f'К сожалению, ничего не нашлось.')


television = System()
television.exec()
