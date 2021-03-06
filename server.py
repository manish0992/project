import flask
from flask import Flask, jsonify, request
from flask_restful import Resource, Api, reqparse
from sqlalchemy.orm import sessionmaker
import uuid

from nltk.classify import NaiveBayesClassifier
from nltk.corpus import subjectivity
from nltk.sentiment import SentimentAnalyzer
from nltk.sentiment.util import *
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk import tokenize
#from nltk_classifier

app = Flask(__name__)
api = Api(app)

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker

#import quesapi

engine = create_engine("mysql://root:root@localhost/myopinion", encoding = 'latin1', echo = True)
Base = declarative_base()

Session = sessionmaker(bind = engine)

class user(Base):
	__tablename__ = 'user_info'
	uid = Column(String(32),  primary_key= True, autoincrement = False)
	username = Column(String(50))
	password = Column(String(50))
	f_name = Column(String(20))
	l_name = Column(String(20))
	age = Column(Integer)
	sex = Column(String(6))
	email_id = Column(String(100))

	

class questions(Base):
	__tablename__ = 'ques_bank'
	q_no = Column(Integer, primary_key = True, autoincrement = True)
	uid = Column(String(32))
	question = Column(String(100))



class Options(Base):
	__tablename__ = 'opt_table'
	op_no = Column(Integer, primary_key = True)
	q_no = Column(Integer)
	optn = Column(String(300))
	opm_result = Column(String(1000))

Base.metadata.create_all(engine, checkfirst = True)
session= Session()

#=======================================================registration api====================================================

parser = reqparse.RequestParser()

parser.add_argument('uname', type = unicode, required = True, location= 'json')
parser.add_argument('pword', type = unicode, required = True, location= 'json')
parser.add_argument('fname', type = unicode, required = True, location= 'json')
parser.add_argument('lname', type = unicode, required = True, location= 'json')
parser.add_argument('age', type = unicode, required = True, location= 'json')
parser.add_argument('gender', type = unicode, required = True, location= 'json')
parser.add_argument('email_id', type = unicode, required = True, location= 'json')


class store_user(Resource):
	def post(self):
		
		args = parser.parse_args()

		for user_valid in session.query(user):
			if (user_valid.username == args['uname']):
				return jsonify(valid_res = "username already exists. Please enter different username")
			if (user_valid.email_id == args['email_id']):
				return jsonify(valid_res = "email id already used. Please enter a different email id") 

			
		unq_id = str(uuid.uuid4()) 
	
		user_data = {'uid' : unq_id, 'username' : args['uname'], 'password' : args['pword'], 'f_name' : args['fname'], 					'l_name' : args['lname'], 'age' : args['age'], 'sex' : args['gender'], 'email_id' : args['email_id']}
		auser = user(uid = user_data['uid'], username = user_data['username'], password = user_data['password'], 
				f_name = user_data['f_name'],l_name = user_data['l_name'], age = user_data['age'], sex = user_data['sex'], 					email_id = user_data['email_id'])
		session.add(auser)
		session.commit()	
		#print auser
		return ({'result' : 'success'})
				#return auser
api.add_resource(store_user, '/user', endpoint='user')

#==================================================login api==========================================================

lparser = reqparse.RequestParser()

lparser.add_argument('username', type = unicode, required = True, location = 'json')
lparser.add_argument('password', type = unicode, required = True, location = 'json')


class login(Resource):
	def post(self):
		largs = lparser.parse_args()
		for auser in session.query(user):
			if(auser.username == largs['username']):
				if(auser.password == largs['password']):
					return jsonify(login_result = 'match found')

			else:
				return jsonify(login_result = 'you have entered wrong username or password!! Please try again...')

api.add_resource(login, '/login', endpoint = 'login')


#================================================= Question table API==========================================	
	


qparser = reqparse.RequestParser()
qparser_put = reqparse.RequestParser()

qparser.add_argument('username', type = unicode, required = True, location = 'json')
qparser.add_argument('question', type = unicode, required = True, location = 'json')

qparser_put.add_argument('question', type = unicode, required = True, location = 'json')


class store_ques(Resource):
	def post(self):
		qargs = qparser.parse_args()
		uname = qargs['username']
		for uid in session.query(user.uid).filter(user.username == uname):
			quid=uid.uid

		ques_data = {'uid' : quid, 'question' : qargs['question']}
		quser = questions(uid = ques_data['uid'], question = ques_data['question'])
		session.add(quser)
		session.commit()
		return ({'result' : 'success'})

	def get(self, i):
		j=i
		dict={}
		for quser in session.query(questions.question)[j:j+3]:
			dict.update({i:quser.question})
			i=i+1
		
		return jsonify(dict)

	def put(self, i):
		qargsp = qparser_put.parse_args()
		session.query(questions).filter(questions.q_no == i).update({questions.question : qargsp['question']})
			#ques.question = qargsp['question']
		
		session.commit()
		return ({'result': 'success'})

	def delete(self, i):
		session.query(questions).filter(questions.q_no == i).delete()
		session.query(questions).filter(questions.q_no > i).update({questions.q_no : questions.q_no - 1})
		session.commit()
		return ({'result': 'success'})



api.add_resource(store_ques, '/ques', endpoint = 'ques')
api.add_resource(store_ques, '/ques/<int:i>', endpoint = 'ques_id')


#============================================================options table API=====================================================
			
oparser = reqparse.RequestParser()

oparser.add_argument('question', type = unicode, required = True, location = 'json')
oparser.add_argument('optn', type = unicode, required = True, location = 'json')

oparser_put = reqparse.RequestParser()
oparser_put.add_argument('option', type = unicode, required = True, location = 'json')
class store_option(Resource):
	def post(self):
		
		oargs = oparser.parse_args()
		quest = oargs['question']
		for ques in session.query(questions.q_no).filter(questions.question == oargs['question']):
			q_no=ques.q_no
		sentences = tokenize.sent_tokenize(oargs['optn'])
		sid = SentimentIntensityAnalyzer()
		nltk_result = ""
		for sentence in sentences:
		     #print(sentence)
		     nltk_result = nltk_result + sentence + "\n"
		     ss = sid.polarity_scores(sentence)
		     for k in sorted(ss):
			 var = ('{0}: {1}, '.format(k, ss[k]) )
			 #print var
		    	 nltk_result = nltk_result + str(var) + "\n"
		option_data = {'q_no' : q_no, 'option' : oargs['optn'], 'result' : nltk_result}
		ouser = Options(q_no = option_data['q_no'], optn = option_data['option'], opm_result = option_data['result'])
		session.add(ouser)
		session.commit()
		return ({'result': 'success'})
		#return jsonify(ouser)

	def get(self, q_no, i):
		j=i
		opt_dict = {}
		for ques in session.query(Options.optn, Options.op_no).filter(Options.q_no == q_no)[j:j+2]:
			opt_dict.update({i:ques.optn})
			i=i+1
		return jsonify(opt_dict)			
			
	def put(self, i):
		oargs = oparser_put.parse_args()
		session.query(Options).filter(Options.op_no == i).update({Options.optn : oargs['option']})
		session.commit()
		return ({'result': 'success'})

	def delete(self, i):
		session.query(Options).filter(Options.op_no == i).delete()
		session.query(Options).filter(Options.op_no > i).update({Options.op_no : Options.op_no - 1})
		session.commit()
		
		return ({'result':'success'})

api.add_resource(store_option, '/option', endpoint = 'option')
api.add_resource(store_option, '/option/<int:i>', endpoint = 'option_post')
api.add_resource(store_option, '/option/<int:q_no>/<int:i>', endpoint = 'option_id')


		 
#=======================================================================================================================								
		
if __name__ == '__main__':
	

	n_instances = 100
	subj_docs = [(sent, 'subj') for sent in subjectivity.sents(categories='subj')[:n_instances]]
	obj_docs = [(sent, 'obj') for sent in subjectivity.sents(categories='obj')[:n_instances]]

	train_subj_docs = subj_docs[:80]
	test_subj_docs = subj_docs[80:100]
	train_obj_docs = obj_docs[:80]
	test_obj_docs = obj_docs[80:100]
	training_docs = train_subj_docs+train_obj_docs
	testing_docs = test_subj_docs+test_obj_docs

	sentim_analyzer = SentimentAnalyzer()
	all_words_neg = sentim_analyzer.all_words([mark_negation(doc) for doc in training_docs])


	unigram_feats = sentim_analyzer.unigram_word_feats(all_words_neg, min_freq=4)
	sentim_analyzer.add_feat_extractor(extract_unigram_feats, unigrams=unigram_feats)

	training_set = sentim_analyzer.apply_features(training_docs)
	test_set = sentim_analyzer.apply_features(testing_docs)

	trainer = NaiveBayesClassifier.train
	classifier = sentim_analyzer.train(trainer, training_set)

	app.run(debug = True, host = '0.0.0.0')
