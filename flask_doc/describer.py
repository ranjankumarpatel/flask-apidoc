# coding=utf8
from functools import wraps

import logging

import datetime
from flask import request
from utils import func_sign

api_forms ={}
api_args = {}

form_data = {}
args_data = {}

class BaseValidator(object):
    """
    基础验证器
    """
    validator = None
    help = None
    def setup(self, validator, helper_string):
        self.validator = validator
        self.help = helper_string

    def __repr__(self):
        return self.help


class StrLenBetween(BaseValidator):
    """
    验证字符串长度
    """
    def __init__(self, min_length, max_length):
        def validator(key, value):
            if value:
                assert isinstance(value, str) or isinstance(value, unicode), u"%s必须是字符串类型, 现在是%s" % (key, type(value))
                assert min_length <= len(value) <= max_length, u"%s的长度必须在%s和%s之间" % (key, min_length, max_length)
        self.setup(validator, u"字符串长度在%s到%s之间" % (min_length, max_length))


class NumberBetween(BaseValidator):
    """
    验证数字范围
    """
    def __init__(self, min_number, max_number):
        def validator(key, value):
            if value:
                assert value.isdigit() or _is_float(value), u"%s必须是数字类型(int或者float)"
                if value.isdigit():
                    assert min_number <= int(value) <= max_number, u"%s的值必须在%s和%s之间" % (key, min_number, max_number)
                if _is_float(value):
                    assert min_number <= float(value) <= max_number, u"%s的值必须在%s和%s之间" % (key, min_number, max_number)
        self.setup(validator, u"值的范围在%s到%s之间" % (min_number, max_number))


class ValidDateTime(BaseValidator):
    """
    验证是合法的日期格式
    """
    def __init__ (self, date_format):
        def validator(key, value):
            if value:
                try:
                    datetime.datetime.strptime(value, date_format)
                except:
                    assert False, u"%s格式不符合[%s] %s" % (key, date_format, value)
        self.setup(validator, u"需符合日期格式[%s]" % date_format)


class ValidEmail(BaseValidator):
    """
    验证是合法的邮箱地址
    """
    def valid_word(self, _str):
        vw = u"qazxswedcvfrtgbnhyujmkiolp1234567890QAZXSWEDCVFRTGBNHYUJMKIOPL.-_~"
        for w in _str:
            if w not in vw:
                return False
        return True

    def __init__(self):
        def validator(key, value):
            if value:
                assert u"@" in value, u"%s需要合法的邮件地址,当前值%s" % (key, value)
                px, domain = value.split(u'@')
                assert self.valid_word(px) and self.valid_word(domain) and len(domain.split(u'.')) >= 2, u"%s需要合法的邮件地址,当前值%s" % (key, value)
        self.setup(validator, u"必须为合法邮件地址")


class ValidUrl(BaseValidator):
    """
    验证是合法的URL
    """
    def __init__(self):
        def validator(key, value):
            if value:
                assert value[:7] == u'http://' or value[:8] == u'https://', u"%s必须为合法URL,当前值%s" % (key, value)
                assert len(value.split(u'.')) >= 2, u"%s必须为合法URL,当前值%s" % (key, value)

        self.setup(validator, u"必须为合法的URL")


def _is_float(s):
    return sum([n.isdigit() for n in s.strip().split('.')]) == 2

def gathering_form(ins):
    """
    生成一个类的实例, 然后将form或者args的内容, 付给这个类实例的属性
    :param ins: 
    :type ins: 
    :return: 
    :rtype: 
    """
    for k, v in form_data.iteritems():
        if v:
            if hasattr(ins, k):
                setattr(ins, k, v)
        else:
            logging.error(u"%s is %s", k, v)
    return ins


def gathering_args(ins):
    """
    生成一个类的实例, 然后将form或者args的内容, 付给这个类实例的属性
    :param ins: 
    :type ins: 
    :return: 
    :rtype: 
    """
    for k, v in args_data.iteritems():
        if v:
            if hasattr(ins, k):
                setattr(ins, k, v)
        else:
            logging.error(u"%s is %s", k, v)
    return ins


class FieldDescribe(object):
    filed_name = ''
    required = True
    data_type = None
    help = ''
    validators = None

    def __repr__(self):
        return u"%s-%s-%s-%s" % (self.filed_name, self.required, self.data_type, self.help)

    def get_arr(self):
        return [self.filed_name, str(self.required), str(self.data_type).split("'")[1], self.help]

    def validate(self, dict):
        value = dict.get(self.filed_name)
        if self.required:
            assert value, u"%s不能为空" % self.filed_name

        if value and self.validators:
            for basevalidator in self.validators:
                basevalidator.validator(self.filed_name, value)

        if self.data_type == type(0.0):
            if value:
                if value.isdigit():
                    return float(value)
                assert _is_float(value), u"%s应该为浮点型,当前值%s" % (self.filed_name, value)
                return float(value)
            else:
                return 0.0
        if self.data_type == type(0):
            if value:
                assert value.isdigit(), u"%s必须为数字,当前值%s" % (self.filed_name, value)
                return int(value)
            else:
                return 0
        return value
        

def regist_fields (f, field_name, required, data_type, help, validators, is_form=False):
    desc = FieldDescribe()
    desc.filed_name = field_name
    desc.required = required
    desc.data_type = data_type
    desc.help = help
    desc.validators = validators
    if validators:
        lines = [u'<ul>']
        for basevalidator in validators:
            lines.append(u"<li>%s</li>" % basevalidator.help)
        lines.append(u"</ul>")
        desc.help = u"%s<br/>%s" % (desc.help, u"\n".join(lines))
    
    f_name = func_sign(f)
    if is_form:
        if f_name in api_forms:
            api_forms[f_name].append(desc)
        else:
            api_forms[f_name] = [desc]
    else:
        if f_name in api_args:
            api_args[f_name].append(desc)
        else:
            api_args[f_name] = [desc]

    return desc

def forms(field_name, required, data_type, help='', validators=None):
    def decorator(f):
        desc = regist_fields(f, field_name, required, data_type, help, validators, is_form=True)
        @wraps(f)
        def d_function(*args, **kwargs):
            value = desc.validate(request.form)
            form_data[field_name] = value
            ret_value = f(*args, **kwargs)
            form_data.clear()
            return ret_value
        return d_function
    return decorator


def args(field_name, required, data_type, help='', validators=None):
    def decorator(f):
        desc = regist_fields(f, field_name, required, data_type, help, validators)
        @wraps(f)
        def d_function (*args, **kwargs):
            value = desc.validate(request.args)
            args_data[field_name] = value
            ret_value = f(*args, **kwargs)
            args_data.clear()
            return ret_value
        return d_function
    return decorator