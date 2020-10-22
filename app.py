import dash
import dash_core_components as dcc
import dash_html_components as html
import os, subprocess,re
from dash.dependencies import Input, Output, State
import base64
import flask
#from OCR import get_my_doc
from flask import send_from_directory
import urllib
#import shutil
import dash_gif_component as Gif


external_stylesheets=['/assets/amyoshinopen.css']
app = dash.Dash(__name__, title = 'Image to Doc', external_stylesheets=external_stylesheets)
server = app.server
server.config['UPLOAD_FOLDER'] = './xtracted_texts'

colors = {
    'background': '#111111',
    'text': '#0392cf',
    'subtext': '#5166A9',
    'jellybean' : "#DE6356",
    'Mellow Apricot' : '#f7b172',
    'Moss Green' : '#83A14D',
    'Dark Cornflower Blue' : '#203d85'
}

app.layout = html.Div(children=[
        html.Div([
            html.H1(children='Image to document converter',
                    style={
                                'textAlign': 'center',
                                'color': colors['Dark Cornflower Blue'],
                            }
                    , className = "twelve columns"),

            html.Div(children='Easily convert your images to editable documents in the blink of an eye!',
                        style={
                                'textAlign': 'center',
                                'color': colors['text'],
                                'fontSize': 18,
                            }
                    , className = 'twelve columns'),
            html.Div(id='mygif',style={'width':'640px','height':'360px','display': 'inline-block'},
                     children=[
                         Gif.GifPlayer(
                             gif='assets/mygif.gif',
                             still='assets/still.jpg',
                         )]
                     ),
            ],className = 'row',style={'textAlign': 'center'}),
        html.Br(),
        html.Br(),
        html.Div(children=[
            html.Div(['Select the language(s) in the image: ']),
            dcc.Dropdown(id='language-dropdown', options=
                [{'label':'English', 'value':'eng'},
                {'label':'Hindi', 'value':'hin'},
                {'label':'Malayalam', 'value':'mal'},
                {'label':'Tamil', 'value':'tam'},
                {'label':'Bengali', 'value':'ben'},
                {'label':'Telugu', 'value':'tel'},
                ], value=['eng'], multi=True),
            html.Div(id='dropdown-output-container'),
            html.Br(),
            html.Br(),
            dcc.Upload(
                    id='upload_image',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select Images')
                    ]),
                    style={
                        'width': '100%',
                        'height': '300px',
                        'borderStyle': 'dashed',
                        'textAlign': 'center',
                        'color' : 'black',
                        'float':'center',
                        'lineHeight': '300px'
                    }, multiple=True),
            html.Div(id="preview_images"),
            html.Br(),
            html.Br(),
            html.Button('Convert', id='convert_button', n_clicks=0, style={'height':"50px", 'width':"150px",
                                                                           'color':colors['text']}),
            html.Br(),
            html.Br(),
            html.P('Download your documents: '),
            html.Button("If downloads links don't appear after 1 minute, click here", id='failsafe', n_clicks=0,
                        style={'height':"35px", 'width':"600px", 'color':colors["Dark Cornflower Blue"]}),
            html.Ul(id="output_results",style={'color':colors["Dark Cornflower Blue"]}),
            html.Br(),
            html.Ul(id='intermediate-div',style={'display':'none'}),
            html.Br(),
            html.Ul(id="output_results_delayed",style={'color':colors["Dark Cornflower Blue"]})
            ],style={
              'margin-left':75, 'margin-right':75,
              'textAlign':'center',
              }
        ),
    ])


@app.callback(
    Output('dropdown-output-container', 'children'),
    [Input('language-dropdown','value')]
)
def selected_language(value):
    return 'You have selected "{}"'.format('+'.join(value))

def show_contents(contents, filename):
    return html.Div([
        # HTML images accept base64 encoded strings in the same format
        # that is supplied by the upload
        html.Img(src=contents, style={'height':'200px', 'width':'150px'}),
        #html.Hr(),
        # html.Div('Raw Content'),
        # html.Pre(contents[0:200] + '...', style={
        #     'whiteSpace': 'pre-wrap',
        #     'wordBreak': 'break-all'
        # })
    ],style={'display': 'inline-block'})

@app.callback(
    Output('preview_images', 'children'),
    [Input('upload_image','filename')],
    [State('upload_image', 'contents')]
)
def preview_img(filename,contents):
    if contents is not None and filename is not None:
        children=[]
        for fname,data in zip(filename,contents):
            try:
                children.append(show_contents(data, fname))
            except Exception as e:
                #print(e)
                return 'There was an error processing this file. Please provide a proper formatted file.'
        return children

@app.server.route("/download")
def download_img():
    value = flask.request.args.get('value')
    filename=urllib.parse.unquote(value).strip()
    #print(filename)
    #print(os.path.exists(os.path.join(server.config['UPLOAD_FOLDER'], filename)))
    return send_from_directory(server.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.callback(
    [Output('output_results', 'children'),
     Output('intermediate-div','children')],
    [Input('convert_button','n_clicks')],
    [State('upload_image','filename'),
    State('upload_image','contents'),
    State('language-dropdown','value')]
)
def get_output(n_clicks,filename,contents,value):
    if n_clicks>0:
        if contents is not None and filename is not None:
            refslist = []
            lang='+'.join(value)
            for fname, data in zip(filename, contents):
                try:
                    """Decode and store a file uploaded with Plotly Dash."""
                    data = data.encode("utf8").split(b";base64,")[1]
                    with open(os.path.join('./input_images', fname), "wb") as fp:
                        fp.write(base64.decodebytes(data))
                    #result_path=get_my_doc(lang,os.path.join('./input_images', fname))
                    result=subprocess.check_output('python OCR.py '+os.path.join('./input_images', fname)+' '+lang, shell=True)
                    result_path = [re.sub(r'[\\n\n]', '', x) for x in str(result).split() if '.docx' in x][0]
                    result_path=re.sub(r'[^A-Za-z0-9:\-./]','',result_path)
                    outfilename=result_path.split('/')[-1]
                    #print(outfilename)
                except Exception as e:
                    #print(e)
                    return ['There was an error processing this file. Please provide a proper formatted file. The name of file must not contain spaces and paranthesis.',
                            'There was an error processing this file. Please provide a proper formatted file. The name of file must not contain spaces and paranthesis.']
                location = "/download?value={}".format(urllib.parse.quote(outfilename))
                refslist.append(html.Li(html.A(fname.split('.')[0], href=location)))
        return refslist,refslist


@app.callback(
    Output('output_results_delayed', 'children'),
    [Input('failsafe','n_clicks')],
    [State('intermediate-div', 'children')]
)
def delayedlinks(n_clicks,children):
    if n_clicks>0:
        return children

if __name__ == '__main__':
    app.run_server(debug=False)
