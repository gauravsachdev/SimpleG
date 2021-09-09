import ipywidgets as ui
from IPython.core.display import display
from IPython.display import FileLink
import sqlite3

from scripts.constants import *
from scripts.mapwidget import CustomMap
import os
from scripts.layerservice import RasterLayerUtil
from model.variableutil import VariableModel
from scripts.DBManager import *

def section(title, contents):
    """Create a collapsible widget container"""

    if type(contents) == str:
        contents = [ui.HTML(value=contents)]

    ret = ui.Accordion(children=tuple([ui.VBox(contents)]))
    ret.set_title(0, title)
    return ret


class View:
    TAB_TITLES = ['Create', 'Manage', 'View', 'About']
    MODEL_DROPDOWN_CREATETAB = ['-','Custom Crops','Custom CornSoy']
    SECTION_TITLE = 'Data'
    DATA_SOURCE_TITLE = 'Source'

    LO10 = ui.Layout(width='10%')
    LO15 = ui.Layout(width='15%')
    LO20 = ui.Layout(width='20%')
    LO25 = ui.Layout(width='25%')
    LOSEL = ui.Layout(width='33%')

    DATA_PRESENT_INDICATOR = '&#x2588'
    DATA_ABSENT_INDICATOR = '&#x2591'

#############################################################################################
    def __init__(self):
        # MVC objects
        self.model = None
        self.ctrl = None

        # User interface widgets

        # General
        self.tabs = None  # Main UI container
        self.debug_output = None
        self.display_object = None
        self.job_selection = []
        
        #Create Tab
        self.model_dd = None
        self.name_tb = None
        self.submit_button = None
        self.description_ta = None
        self.upload_text = None
        self.upload_btn = None
        
        # Manage Tab
        self.instructions_label = None
        self.refresh_btn = None
        self.selectable_window = None
        self.display_btn = None
        self.compare_btn = None
        self.checkboxes = {}
        self.jobs = []
        
        # View Tab 
        self.system_component = None
        self.spatial_resolution = None
        self.type_of_result = None
        self.result_to_view = None
        self.min_max_slider = None
        self.name_dd = None
        self.view_button_submit = None
        self.view_vbox = None
        self.selectable_window_vbox = None
        #About Tab
        #################################

    def intro(self, model, ctrl):
        """Introduce MVC modules to each other"""
        self.ctrl = ctrl
        self.model = model

    def display(self, display_log):
        """Build and show notebook user interface"""
        self.build()

        if display_log:
            self.debug_output = ui.Output(layout={'border': '1px solid black'})

            # noinspection PyTypeChecker
            display(ui.VBox([self.tabs, section('Log', [self.debug_output])]))
        else:
            display(self.tabs)

    def debug(self, text):
        with self.debug_output:
            print(text)

    def build(self):
        """Create user interface"""
        self.tabs = ui.Tab()

        # Set title for each tab
        for i in range(len(self.TAB_TITLES)):
            self.tabs.set_title(i, self.TAB_TITLES[i])

        # Build content (widgets) for each tab
        tab_content = [self.createTab(), self.manageTab(), self.viewTab(), self.testwidget()]

        # Fill with content
        self.tabs.children = tuple(tab_content)

        # Initialize plotter
        #self.ctrl.empty_plot()
    def testwidget(self):
        freq_slider = ui.FloatSlider(value=2.,min=1.,max=10.0,step=0.1,description='Frequency:', readout_format='.1f',) 
       
        content = [section("test slider",[ui.VBox(children=[freq_slider])])]
        return ui.VBox(content)
    
    def createTab(self):
        box_layout = ui.Layout(display='flex',flex_flow='column', align_items='center',width='80%')
        #Dropdown for the model Selction
        self.model_dd=ui.Dropdown(options=self.MODEL_DROPDOWN_CREATETAB,value='-',description='Model:',disabled=False)  
        #Name text Box
        self.name_tb=ui.Text(value='model',placeholder='Name of the model',description='Name:',disabled=False)       
        #Description Text Area
        self.description_ta=ui.Textarea(value='Description',placeholder='Description',description='Description:',disabled=False)       
        #Upload Button
        self.upload_text=ui.Label(value="Configuration File:")
        self.upload_btn=ui.FileUpload(
            accept='',  # Accepted file extension e.g. '.txt', '.pdf', 'image/*', 'image/*,.pdf'
            multiple=False  # True to accept multiple files upload else False
        )
        self.upload_btn.style.button_color = 'gray'
        self.upload_row=ui.HBox([self.upload_text,self.upload_btn])
        #Submit Button
        self.submit_button=ui.Button(description='SUBMIT')
        self.submit_button.style.button_color = 'gray'
        #submit_button.layout = ui.Layout(width="50%")
        #Creating a VBox with the individual widgets
        createTab_widgets = ui.VBox(children=[self.model_dd,self.name_tb,self.description_ta,self.upload_row,self.submit_button],layout=box_layout)
        #createTab_widgets.align_items = 'center'
        content = [section("New Experiment",[ui.VBox(children=[createTab_widgets])])]
        
        #Align things centrally
        box_layout = ui.Layout(display='flex',flex_flow='column', align_items='stretch',width='100%')
        contentvbox = ui.VBox(content,layout=box_layout)
        #contentvbox.layout.align_items = 'center'
        #self.test_btn=ui.Button(description='Test',icon='download')
        return contentvbox
    
    def manageTab(self):
        
        #Label with refresh and instructions
        self.instructions_label=ui.Label(value="Select one model for Display, select two for Compare. After clicking Display/Compare head to the View Tab")
        self.refresh_btn=ui.Button(description="Refresh",disabled=False)
        self.refresh_btn.style.button_color='gray'
        top_box=ui.HBox([self.refresh_btn,self.instructions_label])
        
        #Temporary Database Access will be refreshed with a global variable and the callback function
        dbfile =os.popen("echo $HOME").read().rstrip('\n') + "/SimpleGTool/DatabaseFile(DONOTDELETE).db"
        conn = sqlite3.connect(dbfile)
        cursor = conn.cursor()
        #Database is always created first so the next statement should not give an error
        cursor.execute("SELECT * FROM SIMPLEJobs")
        rows = cursor.fetchall()
        #Storing the contents of the db in list_of_jobs
        list_of_jobs = []
        #For alignment finding the max length of each column
        col_width = max(len(str(word)) for row in rows for word in row) + 2  # padding
        for row in rows:
            str_row = "".join(str(word).ljust(col_width) for word in row)
            list_of_jobs.append(str_row)
        cursor.close()
        conn.close()
        
        #Selectable multiple widget / Checkboxes for each
        self.checkboxes = {}
        self.selectable_window = ui.GridspecLayout(len(rows),11,height="auto")
        row_counter = 0
        #Create a new dictionary key value pair for each jobid and checkbox
        for row in rows:
            self.checkboxes[str(row[0])]=ui.Checkbox(value=False,disabled=False,description="",indent=False,layout=ui.Layout(width="auto",height="auto"))
            self.selectable_window[row_counter,:1] = self.checkboxes[list(self.checkboxes.keys())[-1]]
            self.selectable_window[row_counter,1] = ui.HTML(str(row[0]))
            self.selectable_window[row_counter,2] = ui.HTML(row[6])
            self.selectable_window[row_counter,3:5] = ui.HTML(row[5])
            self.selectable_window[row_counter,5:10] = ui.HTML(row[8])
            self.selectable_window[row_counter,10] = ui.HTML(row[4])
            row_counter = row_counter + 1
        self.checkboxes["0"].disabled = True
            
        #print(self.checkboxes)
        
        #Display Compare Buttons
        self.display_btn=ui.Button(description="Display",disabled=False)
        self.display_btn.style.button_color='gray'
        self.compare_btn=ui.Button(description="Compare",disabled=False)
        self.compare_btn.style.button_color='gray'
        self.bottom_box=ui.HBox([self.display_btn,self.compare_btn])
        self.selectable_window_vbox = ui.VBox(children=[self.selectable_window])
        #Join the widgets
        content=[top_box,section("Compare Tab",[self.selectable_window_vbox]),self.bottom_box]
        contentvbox = ui.VBox(content)
        #contentvbox.layout.align_self = 'center'
        
        #Assign the grid layout to the Vbox and the content
        self.selectable_window.options = list_of_jobs
        return contentvbox
    
    def viewTab(self):
        #Dropdown Menus Change if the Users makes a selection on the System Component Feature
        # Till there is a map on the View Tab there is no change to the dropdowns
        #The functions cb_model_mapping is for this
        #It would also disable some dropdowns if it is of no use
        box_layout = ui.Layout(display='flex',flex_flow='column', align_items='center',width='80%')
        self.system_component=ui.Dropdown(options = ["-","Environment","Land","Production","Water"],value = '-',description='System Component:',disabled=False,style=dict(description_width='initial'))
        
        self.resolution=ui.Dropdown(options = ["-","Geospatial","Regional","Global"],value = '-',description='Spatial Resolution:',disabled=False ,style=dict(description_width='initial'))
        
        self.type_of_result=ui.Dropdown(options = ["-","Absolute Changes","Base Value","Updated Value", "Percent Changes"],value = '-',description='Type of Result:',disabled=False ,style=dict(description_width='initial'))
        
        self.result_to_view = ui.Dropdown(options = ["-","Irrigated","Rainfed"],value = '-',description='Result to View:',disabled=False,style=dict(description_width='initial'))
        
        self.name_dd = ui.Dropdown(options = ["-","Names"],value = '-',description='Model Selection:',disabled=False,style=dict(description_width='initial'))
        
        self.min_max_slider = ui.IntRangeSlider(value=[0,100],min=0,max=100,step=1,description="Range of display",disabled = False, continuous_update=False,orientation = 'horizontal', readout =True, readout_format='d',style=dict(description_width='initial'))
        
        self.view_button_submit = ui.Button(description = 'SUBMIT')
        
        content=section("Select Options for displaying maps",[ui.VBox(children=[self.system_component,self.resolution,self.name_dd,self.result_to_view,self.type_of_result,self.min_max_slider,self.view_button_submit],layout=box_layout)])
        
        map_stuff_testing = '''map_wid = CustomMap("1200px","720px")
        freq_slider = ui.FloatSlider(value=0,min=0,max=100,step=0.1,description='Frequency:', readout_format='.1f',)
        mapbox=section("Map 1",[map_wid])
        id_str = "1"
        system_component="Production"
        spatial_resolution = "Geospatial"
        type_of_result = "PCT"
        result_to_view = "irrigated"
        filter_min = 0
        filter_max = 100

        variable_model = VariableModel(id_str, system_component, spatial_resolution, type_of_result,result_to_view, filter_min, filter_max)


        if variable_model.is_raster():
                layer_util = RasterLayerUtil(variable_model)
                layer = layer_util.create_layer()
                map_wid.visualize_raster(layer, layer_util.processed_raster_path)
        elif variable_model.is_vector():
                layer_util = VectorLayerUtil(variable_model)
                layer = layer_util.create_layer()
        '''
        self.view_button_submit.disabled = True
        self.view_vbox = ui.VBox(children=[content])
        return self.view_vbox
    
    ###################################################
    ###################################################
    ###################################################
    ###################################################
    ###################################################  
    
   