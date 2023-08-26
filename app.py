import numpy as np
import pandas as pd
import pickle
import jsonpickle
from flask import Flask,request,render_template, jsonify
from model import time_standard, old_norm_fwd_bond,bond_categ_logics

app = Flask(__name__,template_folder='templates')

df = pd.read_excel('new_issuance_bucket_ref_data_v_2.xlsx')
df1 = df.copy()

@app.route('/')

def model_output():

    current_fixed_date = pd.to_datetime('2023-04-24',format = '%Y-%m-%d')

    time_standard(df1)

    old_norm_fwd_bond(df1)

    bond_categ_logics(df1)

    return render_template('index.html',tables = [df1.to_html()],titles =[''] )



if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0",port=9696)