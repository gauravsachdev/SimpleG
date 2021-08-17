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
    DDN_PROMPT = 'Please select a data file:'
    DATA_OVERVIEW_TITLE = 'Overview'
    DATA_COVERAGE_TITLE = 'Coverage'
    SEL_INST = 'Select values for query. Use Ctrl (Cmd) key while selecting additional values. Use Shift key to ' \
               'select a range of values. '
    CRITERIA_TITLE = 'Data Selection'
    CRITERIA_APPLY = 'Search'
    OUTPUT_TITLE = 'Results'
    OUTPUT_PRE = 'Limit display to '
    OUTPUT_POST = 'lines'
    EXPORT_BULK_TITLE = 'Export Entire Dataset'
    EXPORT_RESULTS_TITLE = 'Export All Results'
    EXPORT_PLOT_TITLE = 'Export Plot Image'
    EXPORT_BUTTON = 'Create Download '
    EXPORT_LINK_PROMPT = "Click here to save file: "

    PLOT_STATUS_TEMPLATE = """
    <p>NOTE: The plots below will use your most recent query results from the Selection tab.</p>
    <p>Your query, "%s", returned <b>%s</b> records.</p>
    """
    SUMM_PLOT_OPTIONS = ['Values for Model(s) by Scenario', 'Values for Model(s) by Sector',
                         'Values for Model(s) by Region']
    PLOT_PLOT_LABEL = 'Plot:'
    PLOT_NOTE_TITLE = 'Plot Data'
    PLOT_ERROR_MSG = 'ERROR - Cannot generate plot using current options.'
    PLOT_TYPES = [('Line', PLOT_TYPE_LINE), ('Bar', PLOT_TYPE_BAR),
                  ('Histogram', PLOT_TYPE_HIST), ('Box', PLOT_TYPE_BOX)]
    PLOT_TITLE = 'Create Plot'
    PLOT_X_LABEL = 'X Axis:'
    PLOT_Y_LABEL = 'Y Axis:'
    PLOT_TYPE_LABEL = 'Plot Type:'
    PLOT_PIVOT_LABEL = 'Pivot on Field:'
    PLOT_AGGFUNC_LABEL = 'Pivot Aggregation:'
    PLOT_FILL_LABEL = 'Fill missing:'
    PLOT_AGGFUNC_OPTIONS = [AGGF_SUM,
                            AGGF_MEAN,
                            AGGF_COUNT]
    PLOT_FILL_OPTIONS = [(NONE_ITEM, NONE_ITEM),
                         ('Linear Interpolation', FILL_LINEAR),
                         ('Cubic Spline Interpolation', FILL_CUBIC),
                         ('Pad', FILL_PAD)]
    PLOT_HARM_ROW_LABEL = 'Harmonize Row:'
    PLOT_HARM_COL_LABEL = 'Harmonize Column:'
    PLOT_INDEX_LABEL = 'Index:'
    PLOT_GENERATE_LABEL = 'Update Plot'
    PIVOT_TITLE = 'Plot Data'

    DOWNLOAD_DATA_FORMAT_LABEL = 'File Format:'
    DOWNLOAD_DATA_FORMAT_OPTIONS = [
        ('CSV, Comma Separated (.csv)', FORMAT_EXT_CSV),
        ('JSON (.json)', FORMAT_EXT_JSON),
        ('HTML (.html)', FORMAT_EXT_HTML),
        ('Excel (.xls)', FORMAT_EXT_EXCEL),
        ('HDF5 (.h5)', FORMAT_EXT_HDF5),
        ('Pickle, Python (.pickle)', FORMAT_EXT_PICKLE)]

    DOWNLOAD_PLOT_FORMAT_LABEL = 'Image Format:'
    DOWNLOAD_PLOT_FORMAT_OPTIONS = [
        ('Portable Network Graphics (.png)', FORMAT_EXT_PNG),
        ('Scalable Vector Graphics (.svg)', FORMAT_EXT_SVG),
        ('Portable Document Format (.pdf)', FORMAT_EXT_PDF),
        ('JPEG (.jpg)', FORMAT_EXT_JPG)]

    LO10 = ui.Layout(width='10%')
    LO15 = ui.Layout(width='15%')
    LO20 = ui.Layout(width='20%')
    LO25 = ui.Layout(width='25%')
    LOSEL = ui.Layout(width='33%')

    DATA_PRESENT_INDICATOR = '&#x2588'
    DATA_ABSENT_INDICATOR = '&#x2591'


    def __init__(self):
        # MVC objects
        self.model = None
        self.ctrl = None

        # User interface widgets

        # General
        self.tabs = None  # Main UI container
        self.debug_output = None
        self.display_object = None
        
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
        self.checkboxes = []
        self.jobs = []
        
        # View Tab 
        self.system_component = None
        self.spatial_resolution = None
        self.type_of_result = None
        self.result_to_view = None
        self.min_max_slider = None
        self.view_button_submit = None
        self.view_vbox = None
        self.selectable_window_vbox = None
        #About Tab
        #################################
        # Data source, overview, download, and coverage
        self.data_ddn_src = None
        self.desc_output = None
        self.cover_output = None
        self.data_btn_refexp = None
        self.data_out_export = None
        self.data_ddn_format = None

        # Data selection ("filter") widgets
        self.filter_mod = None
        self.filter_scn = None
        self.filter_yrs = None
        self.filter_sec = None
        self.filter_ind = None
        self.filter_reg = None
        self.filter_btn_apply = None
        self.filter_ddn_ndisp = None
        self.filter_output = None
        self.filter_btn_refexp = None
        self.filter_out_export = None
        self.filter_nrec_output = None
        self.filter_ddn_format = None

        # Visualization (plots)
        self.plot_note_html = None
        self.viz_ddn_plot_type = None
        self.viz_ddn_plot_xaxis = None
        self.viz_ddn_plot_yaxis = None
        self.viz_out_plot_output = None
        self.viz_ddn_plot_pivot = None
        self.viz_ddn_plot_aggfunc = None
        self.viz_btn_plot_generate = None
        self.viz_ddn_plot_fill = None
        self.viz_ddn_plot_set = None
        self.viz_out_plot_data = None
        self.viz_ddn_plot_harm_row = None
        self.viz_ddn_plot_harm_col = None
        self.viz_btn_plot_refexp = None
        self.viz_out_plot_export = None
        self.viz_ddn_plot_format = None
        self.viz_ckb_plot_index = None

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
        self.instructions_label=ui.Label(value="Instructions: Select one or model to compare. Click on the first row below in the selectable window for the refresh/changes to work.")
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
        list_of_jobs = []
        col_width = max(len(str(word)) for row in rows for word in row) + 2  # padding
        for row in rows:
            str_row = "".join(str(word).ljust(col_width) for word in row)
            list_of_jobs.append(str_row)
        cursor.close()
        conn.close()
        
        #Selectable multiple widget / Checkboxes for each
        self.checkboxes = []
        self.selectable_window = ui.GridspecLayout(len(rows),11,height="auto")
        row_counter = 0
        for row in rows:
            self.checkboxes.append(ui.Checkbox(value=False,disabled=False,description="",indent=False,layout=ui.Layout(width="auto",height="auto")))
            self.selectable_window[row_counter,:1] = self.checkboxes[-1]
            self.selectable_window[row_counter,1] = ui.HTML(str(row[0]))
            self.selectable_window[row_counter,2] = ui.HTML(row[6])
            self.selectable_window[row_counter,3:5] = ui.HTML(row[5])
            self.selectable_window[row_counter,5:10] = ui.HTML(row[8])
            self.selectable_window[row_counter,10] = ui.HTML(row[4])
            row_counter = row_counter + 1
        self.checkboxes[0].disabled = True
            
            
        
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
        

        self.selectable_window.options = list_of_jobs
        return contentvbox
    
    def viewTab(self):
        box_layout = ui.Layout(display='flex',flex_flow='column', align_items='center',width='80%')
        self.system_component=ui.Dropdown(options = ["-","Environment","Land","Production","Water"],value = '-',description='System Component:',disabled=False,style=dict(description_width='initial'))
        
        self.resolution=ui.Dropdown(options = ["-","Geospatial","Regional","Global"],value = '-',description='Spatial Resolution:',disabled=False ,style=dict(description_width='initial'))
        
        self.type_of_result=ui.Dropdown(options = ["-","Absolute Changes","Base Value","Updated Value", "Percent Changes"],value = '-',description='Type of Result:',disabled=False ,style=dict(description_width='initial'))
        
        self.result_to_view = ui.Dropdown(options = ["-","Irrigated","Rainfed"],value = '-',description='Result to View:',disabled=False,style=dict(description_width='initial'))
        
        self.min_max_slider = ui.IntRangeSlider(value=[0,100],min=0,max=100,step=1,description="Range of display",disabled = False, continuous_update=False,orientation = 'horizontal', readout =True, readout_format='d',style=dict(description_width='initial'))
        
        self.view_button_submit = ui.Button(description = 'SUBMIT')
        
        content=section("Select Options for displaying maps",[ui.VBox(children=[self.system_component,self.resolution,self.type_of_result,self.result_to_view,self.min_max_slider,self.view_button_submit],layout=box_layout)])
        
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
        self.view_vbox = ui.VBox(children=[content])
        return self.view_vbox
    
    ###################################################
    ###################################################
    ###################################################
    ###################################################
    ###################################################  
    def data(self):
        """Create widgets for data tab content"""
        self.data_ddn_src = ui.Dropdown(options=self.model.get_data_options(), value=None)
        self.desc_output = ui.Output(layout={'border': '1px solid black'})
        self.cover_output = ui.Output(layout={'border': '1px solid black'})
        self.data_btn_refexp = ui.Button(description=self.EXPORT_BUTTON, icon='download', layout=self.LO20)
        self.data_out_export = ui.Output(layout={'border': '1px solid black'})
        self.data_ddn_format = ui.Dropdown(value=self.DOWNLOAD_DATA_FORMAT_OPTIONS[0][1],
                                           options=self.DOWNLOAD_DATA_FORMAT_OPTIONS, layout=self.LO25)

        self.update_data_status(self.DATA_NONE)

        content = []

        row = [ui.HTML(value=self.DDN_PROMPT), self.data_ddn_src]

        content.append(section(self.DATA_SOURCE_TITLE, [ui.HBox(row)]))
        content.append(section(self.DATA_OVERVIEW_TITLE, [ui.VBox([self.desc_output])]))
        content.append(section(self.DATA_COVERAGE_TITLE, [ui.VBox([self.cover_output])]))

        # Bulk download

        spacer = ui.Label(value='    ', layout=self.LO10)
        row = ui.HBox([ui.Label(value=self.DOWNLOAD_DATA_FORMAT_LABEL, layout=self.LO10),
                       self.data_ddn_format,
                       spacer,
                       self.data_btn_refexp])

        # TODO Remove temporary note and related lines from code below
        note = ui.Label(value='PLEASE NOTE: This feature is a work in progress. Downloads may time out.',
                        layout=ui.Layout(width='100%', display='flex', alight_items="left"))
        widgets = [ui.VBox([note, row, spacer, self.data_out_export])]
        sec = section(self.EXPORT_BULK_TITLE, widgets)
        sec.selected_index = None  # Collapse due to work-in-progress
        content.append(sec)

        return ui.VBox(content)

    def selection(self):
        """Create widgets for selection tab content"""
        # Create data selection widgets
        self.filter_mod = ui.SelectMultiple(options=[ALL], value=[ALL], rows=5, description=F_MOD,
                                            disabled=False, layout=self.LOSEL)
        self.filter_scn = ui.SelectMultiple(options=[ALL], value=[ALL], rows=5, description=F_SCN,
                                            disabled=False, layout=self.LOSEL)
        self.filter_yrs = ui.SelectMultiple(options=[ALL], value=[ALL], rows=5, description=F_YER,
                                            disabled=False, layout=self.LOSEL)

        self.filter_sec = ui.SelectMultiple(options=[self.ALL_LBLVAL] + SECS, value=[ALL], rows=10,
                                            description=F_SEC, disabled=False, layout=self.LOSEL)
        self.filter_ind = ui.SelectMultiple(options=[self.ALL_LBLVAL] + INDS, value=[ALL], rows=10,
                                            description=F_IND, disabled=False, layout=self.LOSEL)
        self.filter_reg = ui.SelectMultiple(options=[self.ALL_LBLVAL] + REGS, value=[ALL], rows=10,
                                            description=F_REG, disabled=False, layout=self.LOSEL)

        # Create other widgets
        self.filter_btn_apply = ui.Button(description=self.CRITERIA_APPLY, icon='search', layout=self.LO20)
        self.filter_ddn_ndisp = ui.Dropdown(options=['25', '50', '100', ALL], layout=self.LO10)
        self.filter_output = ui.Output()
        self.filter_btn_refexp = ui.Button(description=self.EXPORT_BUTTON, icon='download', layout=self.LO20)
        self.filter_out_export = ui.Output(layout={'border': '1px solid black'})
        self.filter_nrec_output = ui.HTML('')
        self.filter_ddn_format = ui.Dropdown(value=self.DOWNLOAD_DATA_FORMAT_OPTIONS[0][1],
                                             options=self.DOWNLOAD_DATA_FORMAT_OPTIONS, layout=self.LO25)

        content = []

        # Section: Selection criteria

        widgets = [
            (ui.HTML('<div style="text-align: left;">' + self.SEL_INST + '</div>')),
            ui.Label(value='', layout=ui.Layout(width='60%')),
            ui.HBox([
                self.filter_mod,
                self.filter_scn,
                self.filter_yrs]),
            ui.Label(value='', layout=ui.Layout(width='60%')),
            ui.HBox([
                self.filter_reg,
                self.filter_sec,
                self.filter_ind]),
            ui.Label(value='', layout=ui.Layout(width='60%')),
            self.filter_btn_apply
        ]

        content.append(section(self.CRITERIA_TITLE, widgets))

        # Section: Output (with apply button)

        widgets = []
        row = [self.filter_nrec_output,
               ui.HTML('</span><div style="text-align: right;">' + self.OUTPUT_PRE + '</div>', layout=self.LO15),
               self.filter_ddn_ndisp,
               ui.HTML('<div style="text-align: left;">' + self.OUTPUT_POST + '</div>', layout=self.LO10)]
        widgets.append(ui.HBox(row))

        widgets.append(ui.HBox([self.filter_output], layout={'width': '90vw'}))

        content.append(section(self.OUTPUT_TITLE, widgets))

        # Section: Export (download)

        spacer = ui.Label(value='    ', layout=self.LO10)
        row = ui.HBox([ui.Label(value=self.DOWNLOAD_DATA_FORMAT_LABEL, layout=self.LO10),
                       self.filter_ddn_format,
                       spacer,
                       self.filter_btn_refexp])

        widgets = [ui.VBox([row, spacer, self.filter_out_export])]
        content.append(section(self.EXPORT_RESULTS_TITLE, widgets))

        return ui.VBox(content)

    def visualize(self):
        """Create widgets for visualize tab content"""
        content = []

        # Note about data
        self.plot_note_html = ui.HTML(self.PLOT_STATUS_TEMPLATE % (NONE_ITEM, 0))
        content.append(section(self.PLOT_NOTE_TITLE, [self.plot_note_html]))

        # Plotting

        widgets = []

        label = ui.Label(value=self.PLOT_PLOT_LABEL, layout=ui.Layout(display="flex",
                                                                      justify_content="flex-start",
                                                                      width="5%"))
        self.viz_ddn_plot_set = ui.Dropdown(options=PLOT_SET_OPTIONS, layout=self.LO25)
        spacer = ui.Label(value='    ', layout=self.LO10)
        self.viz_btn_plot_generate = ui.Button(description=self.PLOT_GENERATE_LABEL, icon='line-chart', disabled=True,
                                               layout=ui.Layout(width='auto'))
        widgets.append(ui.HBox([label, self.viz_ddn_plot_set, spacer, self.viz_btn_plot_generate]))

        # Settings grid
        w1 = ui.Label(value=self.PLOT_TYPE_LABEL,
                      layout=ui.Layout(width='auto', grid_area='w1'))
        w2 = self.viz_ddn_plot_type = ui.Dropdown(options=self.PLOT_TYPES,
                                                  layout=ui.Layout(width='auto', grid_area='w2'))
        w3 = ui.Label(value=self.PLOT_X_LABEL,
                      layout=ui.Layout(width='auto', grid_area='w3'))
        w4 = self.viz_ddn_plot_xaxis = ui.Dropdown(options=FIELDS,
                                                   layout=ui.Layout(width='auto', grid_area='w4'))
        w5 = ui.Label(value=self.PLOT_Y_LABEL,
                      layout=ui.Layout(width='auto', grid_area='w5'))
        w6 = self.viz_ddn_plot_yaxis = ui.Dropdown(options=FIELDS,
                                                   layout=ui.Layout(width='auto', grid_area='w6'))
        w7 = ui.Label(value=self.PLOT_PIVOT_LABEL,
                      layout=ui.Layout(width='auto', grid_area='w7'))
        w8 = self.viz_ddn_plot_pivot = ui.Dropdown(options=FIELDS,
                                                   layout=ui.Layout(width='auto', grid_area='w8'))
        w9 = ui.Label(value=self.PLOT_AGGFUNC_LABEL,
                      layout=ui.Layout(width='auto', grid_area='w9'))
        w10 = self.viz_ddn_plot_aggfunc = ui.Dropdown(options=[NONE_ITEM] + self.PLOT_AGGFUNC_OPTIONS,
                                                      layout=ui.Layout(width='auto', grid_area='w10'))
        w11 = ui.Label(value=self.PLOT_FILL_LABEL,
                       layout=ui.Layout(width='auto', grid_area='w11'))
        w12 = self.viz_ddn_plot_fill = ui.Dropdown(options=self.PLOT_FILL_OPTIONS,
                                                   layout=ui.Layout(width='auto', grid_area='w12'))
        w13 = ui.Label(value=self.PLOT_INDEX_LABEL, layout=ui.Layout(width='auto', grid_area='w13'))
        w14 = self.viz_ckb_plot_index = ui.Checkbox(indent=False, layout=ui.Layout(width='auto', grid_area='w14'))
        w15 = ui.Label(value=self.PLOT_HARM_ROW_LABEL,
                       layout=ui.Layout(width='auto', grid_area='w15'))
        w16 = self.viz_ddn_plot_harm_row = ui.Dropdown(options=[NONE_ITEM],
                                                       disabled=True,
                                                       layout=ui.Layout(width='auto', grid_area='w16'))
        w17 = ui.Label(value=self.PLOT_HARM_COL_LABEL,
                       layout=ui.Layout(width='auto', grid_area='w17'))
        w18 = self.viz_ddn_plot_harm_col = ui.Dropdown(options=[NONE_ITEM],
                                                       disabled=True,
                                                       layout=ui.Layout(width='auto', grid_area='w18'))
        widgets.append(ui.GridBox(
            children=[w1, w2, w3, w4, w5, w6, w7, w8, w9, w10, w11, w12, w13, w14, w15, w16, w17, w18],
            layout=ui.Layout(
                width='100%',
                grid_template_rows='auto auto auto',
                grid_template_columns='auto auto auto auto auto auto',
                grid_template_areas='''"w3 w4 w7 w8 w15 w16"
                                       "w5 w6 w9 w10 w17 w18"
                                       "w1 w2 w11 w12 w13 w14"''')))

        self.viz_out_plot_output = ui.Output()
        widgets.append(self.viz_out_plot_output)

        content.append(section(self.PLOT_TITLE, widgets))

        # Pivot output
        self.viz_out_plot_data = ui.Output()
        sec = section(self.PIVOT_TITLE, [self.viz_out_plot_data])
        sec.selected_index = None
        content.append(sec)

        # Plot download
        self.viz_ddn_plot_format = ui.Dropdown(value=self.DOWNLOAD_PLOT_FORMAT_OPTIONS[0][1],
                                               options=self.DOWNLOAD_PLOT_FORMAT_OPTIONS, layout=self.LO25)
        self.viz_btn_plot_refexp = ui.Button(description=self.EXPORT_BUTTON, icon='download', layout=self.LO20)
        self.viz_out_plot_export = ui.Output(layout={'border': '1px solid black'})
        spacer = ui.Label(value='    ', layout=self.LO10)
        row = ui.HBox([ui.Label(value=self.DOWNLOAD_PLOT_FORMAT_LABEL, layout=self.LO10),
                       self.viz_ddn_plot_format,
                       spacer,
                       self.viz_btn_plot_refexp])
        widgets = [ui.VBox([row, spacer, self.viz_out_plot_export])]
        content.append(section(self.EXPORT_PLOT_TITLE, widgets))

        return ui.VBox(content)

    def set_harmonize(self, row_options=None, col_options=None, disable=False):
        """Update status and values of harmonize widgets"""
        self.viz_ddn_plot_harm_row.disabled = disable
        self.viz_ddn_plot_harm_col.disabled = disable
        self.viz_ddn_plot_harm_row.options = [NONE_ITEM]
        self.viz_ddn_plot_harm_col.options = [NONE_ITEM]

        if not disable:
            self.viz_ddn_plot_harm_row.options += row_options
            self.viz_ddn_plot_harm_col.options += col_options

    def update_data_status(self, content):
        """Change text in data overview section of data tab"""
        self.desc_output.clear_output(wait=True)

        with self.desc_output:

            if isinstance(content, str):
                # noinspection PyTypeChecker
                display(ui.HTML(content))
            else:
                # Content is dataframe, will show nice html summary
                self.model.set_disp(limit=10)
                display(content)

        # Display data coverage tables

        self.cover_output.clear_output(wait=True)

        html = '&nbsp;'

        if (not isinstance(content, str)) and self.model.valid:

            # First, initialize output by defining styles for table elements
            html = '''
                <style>
                    .vert {
                        writing-mode: vertical-rl;
                        transform: rotate(180deg);
                    }
                    .bot {
                        vertical-align: bottom;
                        line-height: 110%;
                    }
                </style>'''

            # Add legend - covers all tables
            html += '<div style="margin:20px">'
            html += '<p></p>'
            html += '<p>&nbsp;&nbsp;&nbsp;' + self.DATA_PRESENT_INDICATOR + self.DATA_PRESENT_DESC + '</p>'
            html += '<p>&nbsp;&nbsp;&nbsp;' + self.DATA_ABSENT_INDICATOR + self.DATA_ABSENT_DESC + '</p>'

            # One table for each field
            for field in FIELDS[1:-1]:  # ['Scenario', 'Year', 'Sector', 'Region', 'Indicator', 'Unit']:

                html += '<table line-height="110%"><tr><td><b>' + field + '</b>&nbsp;</td>'

                # Column headers: values for field
                for item in sorted(self.model.uniques[field]['']):

                    if not str(item).strip() == '':
                        html += '<td class="bot"><div class="vert"><span>&nbsp;' + str(item) + '</span></div></td>'

                html += '</tr>'

                # Rows: models
                for model in sorted(self.model.mods):
                    html += '<tr style="line-height:150%;"><td style="text-align:right;">' + model + '&nbsp;&nbsp' \
                                                                                                     ';&nbsp;</td> '
                    # Columns: data absent/present indicators
                    for item in self.model.uniques[field]['']:

                        if item in self.model.uniques[field][model]:
                            html += '<td>' + self.DATA_PRESENT_INDICATOR + '</td>'
                        else:
                            html += '<td>' + self.DATA_ABSENT_INDICATOR + '</td>'

                    html += '</tr>'

                html += '</table><br>'

            html += '</div>'

        with self.cover_output:
            # noinspection PyTypeChecker
            display(ui.HTML(html))

    def update_dynamic_selections(self):
        """Populate non-static selection option widgets based on new data"""

        self.filter_mod.options = [ALL] + sorted(list(self.model.mods))
        self.filter_scn.options = [ALL] + sorted(list(self.model.uniques[F_SCN]['']))
        self.filter_yrs.options = [ALL] + sorted(list(self.model.uniques[F_YER]['']))

        self.filter_mod.value = [ALL]
        self.filter_scn.value = [ALL]
        self.filter_yrs.value = [ALL]

    def model_selected(self, mods):
        """React to user changing a filter selection"""
        self.filter_scn.options = self.update_filter('Scenario', mods)

        if ALL in self.filter_scn.options:
            self.filter_scn.value = [ALL]

        # self.filter_yrs.options = self.update_filter('Year', mods)

        if ALL in self.filter_yrs.options:
            self.filter_yrs.value = [ALL]

    def update_filter(self, name, mods):
        """Adjust available filter items based on current selections"""
        self.ctrl.logger.debug('At')

        if mods == ():
            return []
        else:
            setlist = []

            for mod in mods:

                if mod == ALL:
                    setlist = [self.model.uniques[name]['']]
                    break

                setlist.append(self.model.uniques[name][mod])

            return [ALL] + sorted(list(set.intersection(*setlist)))

    def update_filtered_output(self):
        """Display new data in filtered output"""

        self.filter_nrec_output.value = 'Total: <b>' + format(self.model.res_row_count, ',') + '</b> records'

        if self.model.res_row_count < 1:
            self.output(self.EMPTY_LIST_MSG, self.filter_output)
        else:
            # Calc output line limit
            if self.filter_ddn_ndisp.value == ALL:
                limit = self.model.res_row_count
            else:
                limit = int(self.filter_ddn_ndisp.value)

            self.model.set_disp(limit=limit)
            self.output(self.model.results.head(limit), self.filter_output)

    def set_plot_status(self):
        """Change status of plot-related widgets based on availability of filter results"""
        self.ctrl.logger.debug('At')

        # Update plot note
        self.plot_note_html.value = self.PLOT_STATUS_TEMPLATE % (self.model.query,
                                                                 format(self.model.res_row_count, ','))
        if self.model.res_row_count > 0:
            self.viz_btn_plot_generate.disabled = False
        else:
            self.viz_btn_plot_generate.disabled = True
            self.ctrl.empty_plot()

        self.set_harmonize(disable=True)

    def export_msg(self, text, output):
        """Clear export output area then write text to it"""
        self.ctrl.logger.debug('At')
        output.clear_output()

        with output:
            # noinspection PyTypeChecker
            display(ui.HTML('<p>' + text + '</p>'))

    def export_link(self, filepath, output):
        """Create data URI link and add it to export output area"""
        self.ctrl.logger.debug('At')
        output.clear_output()

        link = FileLink(filepath, result_html_prefix=self.EXPORT_LINK_PROMPT)

        with output:
            # noinspection PyTypeChecker
            display(link)

    def output(self, content, widget):
        """Reset output area with contents (text or data)"""
        self.ctrl.logger.debug('At')
        widget.clear_output(wait=True)

        if isinstance(content, str):
            content = ui.HTML(content)

        with widget:
            display(content)
   