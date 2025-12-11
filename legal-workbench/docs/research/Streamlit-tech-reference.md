# STREAMLIT TECHNICAL REFERENCE FOR CLAUDE CODE AGENT
## Version: Streamlit 1.52.0 (December 2025) | Python 3.9-3.14

```xml
<?xml version="1.0" encoding="UTF-8"?>
<streamlit_reference version="1.52.0" date="2025-12">

<!-- ============================================================ -->
<!-- SECTION 1: INPUT WIDGETS                                      -->
<!-- ============================================================ -->
<widgets>

<widget name="st.button">
  <signature>st.button(label, key=None, help=None, on_click=None, args=None, kwargs=None, *, type="secondary", icon=None, disabled=False, use_container_width=None, width="content", shortcut=None)</signature>
  <parameters>
    <param name="label" type="str" required="true">Button label. Supports Markdown (bold, italics, links, images)</param>
    <param name="key" type="str|int" default="None">Unique widget key</param>
    <param name="help" type="str|None" default="None">Tooltip on hover</param>
    <param name="on_click" type="callable" default="None">Callback invoked when clicked</param>
    <param name="args" type="list|tuple" default="None">Args for callback</param>
    <param name="kwargs" type="dict" default="None">Kwargs for callback</param>
    <param name="type" type="str" default="secondary" values="primary|secondary|tertiary">Button styling</param>
    <param name="icon" type="str|None" default="None">Emoji, Material Symbol (:material/icon:), or "spinner"</param>
    <param name="disabled" type="bool" default="False">Disable button</param>
    <param name="width" type="str|int" default="content" values="content|stretch|int">Widget width</param>
    <param name="shortcut" type="str|None" default="None">Keyboard shortcut (e.g., "Ctrl+K", "Enter")</param>
  </parameters>
  <returns type="bool">True only on single rerun after click</returns>
  <session_state>Access via st.session_state[key]. Cannot set button state via Session State API.</session_state>
  <form_behavior>NOT allowed inside forms. Use st.form_submit_button instead.</form_behavior>
  <limitations>Returns True only once per click. State is ephemeral.</limitations>
</widget>

<widget name="st.text_input">
  <signature>st.text_input(label, value="", max_chars=None, key=None, type="default", help=None, autocomplete=None, on_change=None, args=None, kwargs=None, *, placeholder=None, disabled=False, label_visibility="visible", icon=None, width="stretch")</signature>
  <parameters>
    <param name="label" type="str" required="true">Input label</param>
    <param name="value" type="object|None" default='""'>Initial value (cast to str)</param>
    <param name="max_chars" type="int|None" default="None">Maximum characters</param>
    <param name="key" type="str|int" default="None">Widget key</param>
    <param name="type" type="str" default="default" values="default|password">Input type</param>
    <param name="help" type="str|None" default="None">Tooltip</param>
    <param name="autocomplete" type="str" default="varies">HTML autocomplete attribute</param>
    <param name="on_change" type="callable" default="None">Callback on value change</param>
    <param name="placeholder" type="str|None" default="None">Placeholder text</param>
    <param name="disabled" type="bool" default="False">Disable input</param>
    <param name="label_visibility" type="str" default="visible" values="visible|hidden|collapsed">Label visibility</param>
    <param name="icon" type="str|None" default="None">Icon in input field</param>
    <param name="width" type="str|int" default="stretch">Widget width</param>
  </parameters>
  <returns type="str|None">Current value</returns>
</widget>

<widget name="st.text_area">
  <signature>st.text_area(label, value="", height=None, max_chars=None, key=None, help=None, on_change=None, args=None, kwargs=None, *, placeholder=None, disabled=False, label_visibility="visible", width="stretch")</signature>
  <parameters>
    <param name="height" type="int|None" default="None">Height in pixels</param>
  </parameters>
  <returns type="str|None">Current value</returns>
</widget>

<widget name="st.number_input">
  <signature>st.number_input(label, min_value=None, max_value=None, value="min", step=None, format=None, key=None, help=None, on_change=None, args=None, kwargs=None, *, placeholder=None, disabled=False, label_visibility="visible", icon=None, width="stretch")</signature>
  <parameters>
    <param name="min_value" type="int|float|None" default="None">Minimum (default: -(1&lt;&lt;53)+1 for int)</param>
    <param name="max_value" type="int|float|None" default="None">Maximum (default: (1&lt;&lt;53)-1 for int)</param>
    <param name="value" type="int|float|'min'|None" default="min">"min" uses min_value or 0</param>
    <param name="step" type="int|float|None" default="1 for int, 0.01 for float">Stepping interval</param>
    <param name="format" type="str|None" default="None">Printf format (e.g., "%0.2f")</param>
  </parameters>
  <returns type="int|float|None">Current value (type matches value parameter)</returns>
  <limitations>Integers exceeding +/- (1&lt;&lt;53)-1 cannot be accurately stored (JS serialization)</limitations>
</widget>

<widget name="st.selectbox">
  <signature>st.selectbox(label, options, index=0, format_func=str, key=None, help=None, on_change=None, args=None, kwargs=None, *, placeholder=None, disabled=False, label_visibility="visible", accept_new_options=False, width="stretch")</signature>
  <parameters>
    <param name="options" type="Iterable" required="true">Select options</param>
    <param name="index" type="int|None" default="0">Preselected index. None for empty initial state</param>
    <param name="format_func" type="function" default="str">Function to modify display</param>
    <param name="accept_new_options" type="bool" default="False">Allow user to add new options</param>
  </parameters>
  <returns type="any|None">Selected option (copy) or None</returns>
</widget>

<widget name="st.multiselect">
  <signature>st.multiselect(label, options, default=None, format_func=str, key=None, help=None, on_change=None, args=None, kwargs=None, *, max_selections=None, placeholder=None, disabled=False, label_visibility="visible", accept_new_options=False, width="stretch")</signature>
  <parameters>
    <param name="default" type="Iterable|None" default="None">Default selected values</param>
    <param name="max_selections" type="int|None" default="None">Maximum selections allowed</param>
  </parameters>
  <returns type="list">List of selected options (copies)</returns>
</widget>

<widget name="st.slider">
  <signature>st.slider(label, min_value=None, max_value=None, value=None, step=None, format=None, key=None, help=None, on_change=None, args=None, kwargs=None, *, disabled=False, label_visibility="visible", width="stretch")</signature>
  <parameters>
    <param name="min_value" type="int|float|date|time|datetime|None">Defaults: int=0, float=0.0, date=value-14days</param>
    <param name="max_value" type="int|float|date|time|datetime|None">Defaults: int=100, float=1.0, date=value+14days</param>
    <param name="value" type="type|tuple|list|None">Initial value. Tuple/list creates range slider</param>
    <param name="step" type="int|float|timedelta|None">Defaults: int=1, float=0.01, date=1day, time=15min</param>
    <param name="format" type="str|None">Printf for numbers, momentJS for dates (e.g., "MM/DD/YY")</param>
  </parameters>
  <returns type="value_type|tuple">Current value(s)</returns>
  <supported_types>int, float, date, time, datetime</supported_types>
</widget>

<widget name="st.select_slider">
  <signature>st.select_slider(label, options=(), value=None, format_func=str, key=None, help=None, on_change=None, args=None, kwargs=None, *, disabled=False, label_visibility="visible", width="stretch")</signature>
  <returns type="any|tuple">Selected value(s)</returns>
  <difference>Accepts any datatype with iterable options vs numeric/date ranges only</difference>
</widget>

<widget name="st.checkbox">
  <signature>st.checkbox(label, value=False, key=None, help=None, on_change=None, args=None, kwargs=None, *, disabled=False, label_visibility="visible", width="content")</signature>
  <returns type="bool">Whether checkbox is checked</returns>
</widget>

<widget name="st.toggle">
  <signature>st.toggle(label, value=False, key=None, help=None, on_change=None, args=None, kwargs=None, *, disabled=False, label_visibility="visible", width="content")</signature>
  <returns type="bool">Whether toggle is on</returns>
</widget>

<widget name="st.radio">
  <signature>st.radio(label, options, index=0, format_func=str, key=None, help=None, on_change=None, args=None, kwargs=None, *, disabled=False, horizontal=False, captions=None, label_visibility="visible", width="content")</signature>
  <parameters>
    <param name="horizontal" type="bool" default="False">Orient options horizontally</param>
    <param name="captions" type="iterable|None" default="None">Captions below each option</param>
  </parameters>
  <returns type="any|None">Selected option (copy) or None</returns>
</widget>

<widget name="st.date_input">
  <signature>st.date_input(label, value="today", min_value=None, max_value=None, key=None, help=None, on_change=None, args=None, kwargs=None, *, format="YYYY/MM/DD", disabled=False, label_visibility="visible", width="stretch")</signature>
  <parameters>
    <param name="value" type="'today'|date|datetime|str|list|tuple|None" default="today">List/tuple for date range</param>
    <param name="format" type="str" default="YYYY/MM/DD" values="DD/MM/YYYY|MM/DD/YYYY">Display format</param>
  </parameters>
  <returns type="date|tuple">Selected date(s)</returns>
</widget>

<widget name="st.time_input">
  <signature>st.time_input(label, value="now", key=None, help=None, on_change=None, args=None, kwargs=None, *, disabled=False, label_visibility="visible", step=900, width="stretch")</signature>
  <parameters>
    <param name="step" type="int|timedelta" default="900">Stepping interval in seconds (60-82800)</param>
  </parameters>
  <returns type="time|None">Selected time</returns>
</widget>

<widget name="st.file_uploader">
  <signature>st.file_uploader(label, type=None, accept_multiple_files=False, key=None, help=None, on_change=None, args=None, kwargs=None, *, disabled=False, label_visibility="visible", width="stretch")</signature>
  <parameters>
    <param name="type" type="str|list|None" default="None">Allowed extensions (e.g., "csv", ["jpg", "png"])</param>
    <param name="accept_multiple_files" type="bool|'directory'" default="False">"directory" for folder upload</param>
  </parameters>
  <returns type="None|UploadedFile|list">UploadedFile is BytesIO subclass</returns>
  <limitations>Default max 200MB (server.maxUploadSize). Files in RAM.</limitations>
</widget>

<widget name="st.camera_input">
  <signature>st.camera_input(label, key=None, help=None, on_change=None, args=None, kwargs=None, *, disabled=False, label_visibility="visible")</signature>
  <returns type="UploadedFile|None">Image file (BytesIO) or None</returns>
</widget>

<widget name="st.color_picker">
  <signature>st.color_picker(label, value=None, key=None, help=None, on_change=None, args=None, kwargs=None, *, disabled=False, label_visibility="visible", width="content")</signature>
  <parameters>
    <param name="value" type="str|None" default="#000000">Initial hex color</param>
  </parameters>
  <returns type="str">Hex color string (e.g., "#00f900")</returns>
</widget>

<widget name="st.data_editor">
  <signature>st.data_editor(data, *, width=None, height=None, use_container_width=True, hide_index=None, column_order=None, column_config=None, num_rows="fixed", disabled=False, key=None, on_change=None, args=None, kwargs=None)</signature>
  <parameters>
    <param name="column_config" type="dict|None" default="None">Column configuration via st.column_config</param>
    <param name="num_rows" type="str" default="fixed" values="fixed|dynamic">"dynamic" allows add/delete</param>
    <param name="disabled" type="bool|Iterable" default="False">True for all, or list of column names</param>
  </parameters>
  <returns type="DataFrame">Edited data (copy)</returns>
</widget>

</widgets>

<!-- ============================================================ -->
<!-- SECTION 2: LAYOUT AND CONTAINERS                              -->
<!-- ============================================================ -->
<layout>

<component name="st.columns">
  <signature>st.columns(spec, *, gap="small", vertical_alignment="top", border=False, width="stretch")</signature>
  <parameters>
    <param name="spec" type="int|list" required="true">Number of columns or proportions [3,1]</param>
    <param name="gap" type="str|None" default="small" values="small|medium|large|None">Gap between columns (1rem/2rem/4rem/none)</param>
    <param name="vertical_alignment" type="str" default="top" values="top|center|bottom">Vertical alignment</param>
    <param name="border" type="bool" default="False">Show borders (consistent heights)</param>
  </parameters>
  <returns type="list">List of container objects</returns>
  <usage>col1, col2 = st.columns(2); with col1: st.write("...")</usage>
  <responsive>Columns stack vertically on narrow viewports</responsive>
  <nesting>Don't nest more than once for best appearance</nesting>
</component>

<component name="st.container">
  <signature>st.container(*, border=None, key=None, width="stretch", height="content", horizontal=False, horizontal_alignment="left", vertical_alignment="top", gap="small")</signature>
  <parameters>
    <param name="border" type="bool|None" default="None">Default True if height fixed</param>
    <param name="key" type="str|None" default="None">Also CSS class prefix: st-key-{key}</param>
    <param name="height" type="str|int" default="content" values="content|stretch|int">Fixed height enables scrolling</param>
    <param name="horizontal" type="bool" default="False">Enable horizontal flexbox</param>
    <param name="horizontal_alignment" type="str" default="left" values="left|center|right|distribute">Alignment</param>
    <param name="gap" type="str|None" default="small">Minimum gap between elements</param>
  </parameters>
  <returns type="container">Container object</returns>
</component>

<component name="st.expander">
  <signature>st.expander(label, expanded=False, *, icon=None, width="stretch")</signature>
  <parameters>
    <param name="label" type="str" required="true">Header text</param>
    <param name="expanded" type="bool" default="False">Initial state</param>
    <param name="icon" type="str|None" default="None">Emoji or :material/icon:</param>
  </parameters>
  <performance>Content computed EVEN IF COLLAPSED</performance>
</component>

<component name="st.tabs">
  <signature>st.tabs(tabs, *, width="stretch", default=None)</signature>
  <parameters>
    <param name="tabs" type="list[str]" required="true">Tab labels</param>
    <param name="default" type="str|None" default="None">Default tab by label</param>
  </parameters>
  <returns type="list">List of container objects</returns>
  <performance>ALL tab content computed regardless of selection</performance>
</component>

<component name="st.sidebar">
  <signature>st.sidebar</signature>
  <usage>st.sidebar.selectbox(...) OR with st.sidebar: st.radio(...)</usage>
  <width_control>Resizable via drag. st.set_page_config(initial_sidebar_state="expanded|collapsed|auto")</width_control>
  <unsupported_object_notation>st.echo, st.spinner, st.toast (use 'with' notation)</unsupported_object_notation>
</component>

<component name="st.popover">
  <signature>st.popover(label, *, type="secondary", help=None, icon=None, disabled=False, use_container_width=None, width="content")</signature>
  <parameters>
    <param name="type" type="str" default="secondary" values="primary|secondary|tertiary">Button styling</param>
  </parameters>
  <behavior>Opening/closing does NOT trigger rerun. Widget interactions inside DO trigger rerun.</behavior>
</component>

<component name="st.dialog">
  <signature>@st.dialog(title, *, width="small", dismissible=True, on_dismiss="ignore")</signature>
  <parameters>
    <param name="title" type="str" required="true">Modal title (cannot be empty)</param>
    <param name="width" type="str" default="small" values="small|medium|large">500px/750px/1280px max</param>
    <param name="dismissible" type="bool" default="True">User can dismiss via X, ESC, outside click</param>
    <param name="on_dismiss" type="str|callable" default="ignore" values="ignore|rerun|callable">Response to dismissal</param>
  </parameters>
  <usage>@st.dialog("Title"); def my_dialog(): ...; if st.button("Open"): my_dialog()</usage>
  <closing>Call st.rerun() inside dialog function to close</closing>
  <limitations>Only ONE dialog open at a time. Cannot call st.sidebar inside dialog.</limitations>
</component>

<component name="st.form">
  <signature>st.form(key, *, clear_on_submit=False, enter_to_submit=True, border=True, height=None)</signature>
  <parameters>
    <param name="key" type="str" required="true">Unique form identifier</param>
    <param name="clear_on_submit" type="bool" default="False">Reset widgets after submit</param>
    <param name="enter_to_submit" type="bool" default="True">Enter in text_input submits</param>
  </parameters>
  <submit_button>st.form_submit_button(label="Submit", *, help=None, on_click=None, args=None, kwargs=None, type="secondary", icon=None, disabled=False, use_container_width=False)</submit_button>
  <constraints>st.button/download_button NOT allowed. Only form_submit_button can have callbacks.</constraints>
  <behavior>No reruns until submit. Batches all changes.</behavior>
</component>

<component name="st.empty">
  <signature>st.empty()</signature>
  <description>Single-element container. Each new element replaces previous.</description>
  <methods>placeholder.empty(), placeholder.{element}(), placeholder.container()</methods>
</component>

</layout>

<!-- ============================================================ -->
<!-- SECTION 3: CHARTS AND VISUALIZATION                           -->
<!-- ============================================================ -->
<charts>

<chart name="st.line_chart">
  <signature>st.line_chart(data=None, *, x=None, y=None, x_label=None, y_label=None, color=None, width="stretch", height="content", use_container_width=None)</signature>
  <parameters>
    <param name="data" type="DataFrame|array|dict">Data to plot</param>
    <param name="x" type="str|None">Column for x-axis. None uses index</param>
    <param name="y" type="str|Sequence[str]|None">Column(s) for y-axis</param>
    <param name="color" type="str|tuple|Sequence">Line colors (hex, RGB, column name)</param>
  </parameters>
  <notes>Syntax-sugar around st.altair_chart. use_container_width DEPRECATED.</notes>
</chart>

<chart name="st.area_chart">
  <signature>st.area_chart(data=None, *, x=None, y=None, x_label=None, y_label=None, color=None, stack=True, width="stretch", height="content")</signature>
  <parameters>
    <param name="stack" type="bool|str" default="True" values="True|False|normalize|center">Stacking behavior</param>
  </parameters>
</chart>

<chart name="st.bar_chart">
  <signature>st.bar_chart(data=None, *, x=None, y=None, x_label=None, y_label=None, color=None, horizontal=False, stack=True, sort=None, width="stretch", height="content")</signature>
  <parameters>
    <param name="horizontal" type="bool" default="False">Horizontal bars</param>
    <param name="stack" type="bool|str" default="True" values="True|False|normalize">Stacking</param>
  </parameters>
</chart>

<chart name="st.scatter_chart">
  <signature>st.scatter_chart(data=None, *, x=None, y=None, x_label=None, y_label=None, color=None, size=None, width="stretch", height="content")</signature>
  <parameters>
    <param name="size" type="str|float|int|None">Point size (number or column name)</param>
  </parameters>
</chart>

<chart name="st.map">
  <signature>st.map(data=None, *, latitude=None, longitude=None, color=None, size=None, zoom=None, width="stretch", height=500)</signature>
  <parameters>
    <param name="latitude" type="str|None">Column name. Auto-detects: lat, latitude, LAT</param>
    <param name="longitude" type="str|None">Column name. Auto-detects: lon, longitude, LON</param>
    <param name="size" type="str|float|None">Point size in meters</param>
  </parameters>
</chart>

<chart name="st.pyplot">
  <signature>st.pyplot(fig=None, clear_figure=None, *, width="stretch", **kwargs)</signature>
  <parameters>
    <param name="fig" type="matplotlib.figure.Figure">Matplotlib figure</param>
    <param name="clear_figure" type="bool|None">Clear after rendering</param>
  </parameters>
  <requirements>matplotlib>=3.0.0</requirements>
  <warning>Not thread-safe. Use threading.RLock for concurrent users.</warning>
</chart>

<chart name="st.altair_chart">
  <signature>st.altair_chart(altair_chart, *, width=None, height="content", theme="streamlit", key=None, on_select="ignore", selection_mode=None)</signature>
  <parameters>
    <param name="theme" type="str|None" default="streamlit" values="streamlit|None">Theme</param>
    <param name="on_select" type="str|callable" default="ignore" values="ignore|rerun|callable">Selection handling</param>
    <param name="selection_mode" type="str|Iterable|None">Which selection params to use</param>
  </parameters>
  <selection_events>point_selection (click), interval_selection (drag)</selection_events>
</chart>

<chart name="st.plotly_chart">
  <signature>st.plotly_chart(figure_or_data, *, width="stretch", height="content", theme="streamlit", key=None, on_select="ignore", selection_mode=('points', 'box', 'lasso'), config=None)</signature>
  <parameters>
    <param name="selection_mode" type="str|tuple" default="('points', 'box', 'lasso')">Allowed modes</param>
    <param name="config" type="dict|None">Plotly config (scrollZoom, displayModeBar, etc.)</param>
  </parameters>
  <requirements>plotly>=4.0.0</requirements>
</chart>

<chart name="st.pydeck_chart">
  <signature>st.pydeck_chart(pydeck_obj=None, *, width="stretch", height=500, selection_mode="single-object", on_select="ignore", key=None)</signature>
  <parameters>
    <param name="selection_mode" type="str" default="single-object" values="single-object|multi-object">Selection</param>
  </parameters>
  <requirements>Layers need pickable=True and id for stateful selections</requirements>
  <warning>Uses 2 WebGL contexts per chart. Limit to 8 per page.</warning>
</chart>

<chart name="st.graphviz_chart">
  <signature>st.graphviz_chart(figure_or_dot, *, width=None)</signature>
  <parameters>
    <param name="figure_or_dot" type="graphviz.Graph|str">Graphviz object or DOT string</param>
  </parameters>
  <requirements>graphviz>=0.19.0</requirements>
</chart>

<streaming name="add_rows" status="DEPRECATED">
  <signature>element.add_rows(data=None, **kwargs)</signature>
  <supported>line_chart, area_chart, bar_chart, scatter_chart, map, altair_chart, vega_lite_chart</supported>
</streaming>

</charts>

<!-- ============================================================ -->
<!-- SECTION 4: DATA CONNECTIONS AND CACHING                       -->
<!-- ============================================================ -->
<data>

<connection name="st.connection">
  <signature>st.connection(name, type=None, max_entries=None, ttl=None, **kwargs)</signature>
  <parameters>
    <param name="name" type="str">Connection name for secrets [connections.{name}]</param>
    <param name="type" type="str|class|None">sql, snowflake, or custom class</param>
    <param name="ttl" type="float|timedelta|None">Cache expiration</param>
  </parameters>
  <builtin_types>
    <type name="sql" class="st.connections.SQLConnection">
      <methods>query(sql, *, ttl, show_spinner), connect(), reset()</methods>
      <attributes>engine, session, driver</attributes>
    </type>
    <type name="snowflake" class="st.connections.SnowflakeConnection">
      <methods>query(sql), session(), cursor(), write_pandas(), reset()</methods>
    </type>
  </builtin_types>
</connection>

<custom_connection name="BaseConnection">
  <signature>st.connections.BaseConnection(connection_name, **kwargs)</signature>
  <required_methods>
    <method name="_connect(self, **kwargs)">Must implement. Returns underlying connection.</method>
  </required_methods>
  <properties>_instance, _secrets</properties>
  <registration>st.connection("name", type=MyConnection) or type="mymodule.MyConnection"</registration>
</custom_connection>

<secrets name="st.secrets">
  <file_locations>
    <local>.streamlit/secrets.toml</local>
    <global>~/.streamlit/secrets.toml</global>
    <precedence>Working directory > Global</precedence>
  </file_locations>
  <access_patterns>
    st.secrets["key"]
    st.secrets.key
    st.secrets["section"]["key"]
    st.secrets.section.key
    **st.secrets.section (spread as kwargs)
  </access_patterns>
  <security>Never commit to version control. Add to .gitignore.</security>
</secrets>

<caching name="@st.cache_data">
  <signature>@st.cache_data(func=None, *, ttl=None, max_entries=None, show_spinner=True, show_time=False, persist=None, hash_funcs=None)</signature>
  <parameters>
    <param name="ttl" type="float|timedelta|str|None">Expiration. "1h", "1d", timedelta(hours=1)</param>
    <param name="max_entries" type="int|None">Max cached entries</param>
    <param name="persist" type="str|bool|None" values="disk|True|None">Persist to disk</param>
    <param name="hash_funcs" type="dict|None">Custom hash {type: func}</param>
  </parameters>
  <use_cases>DataFrames, API responses, serializable data</use_cases>
  <clearing>func.clear(), func.clear(*args), st.cache_data.clear()</clearing>
  <unhashable>Prefix arg with underscore: def func(_db_conn, query)</unhashable>
</caching>

<caching name="@st.cache_resource">
  <signature>@st.cache_resource(func=None, *, ttl=None, max_entries=None, show_spinner=True, show_time=False, validate=None, hash_funcs=None)</signature>
  <parameters>
    <param name="validate" type="callable|None">Validation func. Returns False = recompute</param>
  </parameters>
  <use_cases>DB connections, ML models, singletons</use_cases>
  <behavior>Returns SAME object (shared across sessions). Must be thread-safe.</behavior>
</caching>

<data_display name="st.dataframe">
  <signature>st.dataframe(data=None, width="stretch", height="auto", *, hide_index=None, column_order=None, column_config=None, key=None, on_select="ignore", selection_mode="multi-row", row_height=None, placeholder=None)</signature>
  <parameters>
    <param name="selection_mode" type="str|Iterable" default="multi-row" values="multi-row|single-row|multi-column|single-column|multi-cell|single-cell">Selection</param>
  </parameters>
  <returns>When on_select != "ignore": dict with selection.rows, selection.columns, selection.cells</returns>
</data_display>

<column_config namespace="st.column_config">
  <types>
    <type name="Column">st.column_config.Column(label=None, *, width=None, help=None, disabled=None, required=None)</type>
    <type name="TextColumn">st.column_config.TextColumn(..., max_chars=None, validate=None)</type>
    <type name="NumberColumn">st.column_config.NumberColumn(..., min_value=None, max_value=None, step=None, format=None)</type>
    <type name="CheckboxColumn">st.column_config.CheckboxColumn(...)</type>
    <type name="SelectboxColumn">st.column_config.SelectboxColumn(..., options=None)</type>
    <type name="DatetimeColumn">st.column_config.DatetimeColumn(..., min_value=None, max_value=None, format=None, timezone=None)</type>
    <type name="DateColumn">st.column_config.DateColumn(...)</type>
    <type name="TimeColumn">st.column_config.TimeColumn(...)</type>
    <type name="LinkColumn">st.column_config.LinkColumn(..., display_text=None)</type>
    <type name="ImageColumn">st.column_config.ImageColumn(...)</type>
    <type name="ProgressColumn">st.column_config.ProgressColumn(..., min_value=None, max_value=None)</type>
    <type name="LineChartColumn">st.column_config.LineChartColumn(..., y_min=None, y_max=None)</type>
    <type name="BarChartColumn">st.column_config.BarChartColumn(...)</type>
  </types>
  <usage>column_config={"col": None} hides, {"col": "Label"} renames</usage>
</column_config>

</data>

<!-- ============================================================ -->
<!-- SECTION 5: MEDIA AND CHAT ELEMENTS                            -->
<!-- ============================================================ -->
<media>

<element name="st.image">
  <signature>st.image(image, caption=None, width="content", clamp=False, channels="RGB", output_format="auto")</signature>
  <parameters>
    <param name="image" type="ndarray|BytesIO|str|Path|list">URL, path, bytes, numpy, PIL Image</param>
    <param name="width" type="str|int" default="content" values="content|stretch|int">Display width</param>
    <param name="channels" type="str" default="RGB" values="RGB|BGR">Use BGR for OpenCV</param>
    <param name="output_format" type="str" default="auto" values="JPEG|PNG|auto">Transfer format</param>
  </parameters>
  <formats>PNG, JPEG, GIF, SVG, WebP</formats>
</element>

<element name="st.audio">
  <signature>st.audio(data, format="audio/wav", start_time=0, *, sample_rate=None, end_time=None, loop=False, autoplay=False, width="stretch")</signature>
  <parameters>
    <param name="sample_rate" type="int|None">Required only for NumPy arrays</param>
    <param name="start_time" type="int|float|timedelta|str">int/float=seconds, str="2 minute"</param>
  </parameters>
  <formats>WAV, MP3, OGG</formats>
</element>

<element name="st.video">
  <signature>st.video(data, format="video/mp4", start_time=0, *, subtitles=None, end_time=None, loop=False, autoplay=False, muted=False, width="stretch")</signature>
  <parameters>
    <param name="subtitles" type="str|bytes|Path|dict|None">.vtt/.srt path, content, or {"English": "en.vtt"}</param>
    <param name="muted" type="bool" default="False">Required with autoplay=True for auto-autoplay</param>
  </parameters>
  <formats>MP4 (H.264), WebM, OGG</formats>
</element>

<element name="st.logo">
  <signature>st.logo(image, *, link=None, icon_image=None)</signature>
  <parameters>
    <param name="image" type="str|Path|PIL.Image|ndarray">Logo for sidebar</param>
    <param name="icon_image" type="same|None">Smaller icon for main body</param>
  </parameters>
</element>

</media>

<chat>

<element name="st.chat_message">
  <signature>st.chat_message(name, *, avatar=None, width="stretch")</signature>
  <parameters>
    <param name="name" type="str" values="user|assistant|ai|human|custom">Message author</param>
    <param name="avatar" type="str|None">Emoji, :material/icon:, URL, "spinner", or path</param>
  </parameters>
  <usage>with st.chat_message("assistant"): st.write("...")</usage>
</element>

<element name="st.chat_input">
  <signature>st.chat_input(placeholder="Your message", *, key=None, max_chars=None, accept_file=False, file_type=None, accept_audio=False, audio_sample_rate=16000, disabled=False, on_submit=None, args=None, kwargs=None, width="stretch")</signature>
  <parameters>
    <param name="accept_file" type="bool|str" default="False" values="False|True|multiple|directory">File upload</param>
    <param name="accept_audio" type="bool" default="False">Enable audio recording</param>
    <param name="audio_sample_rate" type="int" default="16000" values="8000|11025|16000|22050|24000|32000|44100|48000">Sample rate</param>
  </parameters>
  <returns>
    str (text only) OR dict-like {.text, .files, .audio} when accepting files/audio
  </returns>
  <positioning>Pinned to bottom in main body. Inline in containers/sidebar.</positioning>
</element>

<pattern name="chat_history">
  <code>
if "messages" not in st.session_state:
    st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
if prompt := st.chat_input("..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("assistant"):
        response = st.write_stream(generate_response(prompt))
    st.session_state.messages.append({"role": "assistant", "content": response})
  </code>
</pattern>

</chat>

<!-- ============================================================ -->
<!-- SECTION 6: STATUS AND TEXT ELEMENTS                           -->
<!-- ============================================================ -->
<status>

<element name="st.progress">
  <signature>st.progress(value, text=None)</signature>
  <parameters>
    <param name="value" type="int|float">0-100 (int) or 0.0-1.0 (float)</param>
  </parameters>
  <methods>progress(value, text=None), empty()</methods>
</element>

<element name="st.spinner">
  <signature>st.spinner(text="In progress...", *, show_time=False)</signature>
  <usage>with st.spinner("..."): long_operation()</usage>
</element>

<element name="st.status">
  <signature>st.status(label, *, expanded=False, state="running", width="stretch")</signature>
  <parameters>
    <param name="state" type="str" default="running" values="running|complete|error">Icon state</param>
  </parameters>
  <methods>update(*, label=None, expanded=None, state=None)</methods>
  <behavior>Auto-updates to "complete" at end of with block</behavior>
</element>

<element name="st.toast">
  <signature>st.toast(body, *, icon=None, duration=4000)</signature>
  <parameters>
    <param name="duration" type="int" default="4000">Display duration in ms</param>
  </parameters>
</element>

<element name="st.success"><signature>st.success(body, *, icon="✅", width="stretch")</signature></element>
<element name="st.info"><signature>st.info(body, *, icon="ℹ️", width="stretch")</signature></element>
<element name="st.warning"><signature>st.warning(body, *, icon="⚠️", width="stretch")</signature></element>
<element name="st.error"><signature>st.error(body, *, icon="🚨", width="stretch")</signature></element>
<element name="st.exception"><signature>st.exception(exception)</signature></element>
<element name="st.balloons"><signature>st.balloons()</signature></element>
<element name="st.snow"><signature>st.snow()</signature></element>

</status>

<text>

<element name="st.write">
  <signature>st.write(*args, unsafe_allow_html=False)</signature>
  <type_handling>
    str → st.markdown()
    DataFrame/dict/list → st.dataframe()
    Exception → st.exception()
    function/module → st.help()
    Altair → st.altair_chart()
    Matplotlib → st.pyplot()
    Plotly → st.plotly_chart()
    PIL.Image → st.image()
    generator → st.write_stream()
  </type_handling>
</element>

<element name="st.markdown">
  <signature>st.markdown(body, unsafe_allow_html=False, *, help=None, width="stretch", text_alignment="left")</signature>
  <features>
    Emoji: :sunglasses:
    Material icons: :material/icon_name:
    LaTeX: $inline$ or $$block$$
    Colored: :red[text] :blue-background[text]
    Badges: :orange-badge[text]
    Small: :small[text]
  </features>
</element>

<element name="st.title"><signature>st.title(body, anchor=None, *, help=None, divider=False)</signature></element>
<element name="st.header"><signature>st.header(body, anchor=None, *, help=None, divider=False)</signature></element>
<element name="st.subheader"><signature>st.subheader(body, anchor=None, *, help=None, divider=False)</signature></element>
<element name="st.caption"><signature>st.caption(body, unsafe_allow_html=False, *, help=None)</signature></element>

<element name="st.code">
  <signature>st.code(body, language="python", *, line_numbers=False, wrap_lines=False)</signature>
</element>

<element name="st.latex">
  <signature>st.latex(body, *, help=None)</signature>
  <supported>katex.org/docs/supported.html</supported>
</element>

<element name="st.html">
  <signature>st.html(body, *, height=None, scrolling=False, unsafe_allow_javascript=False)</signature>
</element>

</text>

<!-- ============================================================ -->
<!-- SECTION 7: CONFIGURATION                                      -->
<!-- ============================================================ -->
<configuration>

<hierarchy>
  1. Global: ~/.streamlit/config.toml
  2. Project: .streamlit/config.toml
  3. Environment: STREAMLIT_SERVER_PORT
  4. CLI: --server.port=8501
</hierarchy>

<section name="[global]">
  <option name="disableWidgetStateDuplicationWarning" type="bool" default="false"/>
  <option name="showWarningOnDirectExecution" type="bool" default="true"/>
</section>

<section name="[logger]">
  <option name="level" type="str" default="info" values="error|warning|info|debug"/>
  <option name="messageFormat" type="str" default="%(asctime)s %(message)s"/>
</section>

<section name="[client]">
  <option name="showErrorDetails" type="str" default="full" values="full|stacktrace|type|none"/>
  <option name="toolbarMode" type="str" default="auto" values="auto|developer|viewer|minimal"/>
  <option name="showSidebarNavigation" type="bool" default="true"/>
</section>

<section name="[runner]">
  <option name="magicEnabled" type="bool" default="true"/>
  <option name="fastReruns" type="bool" default="true"/>
  <option name="enforceSerializableSessionState" type="bool" default="false"/>
</section>

<section name="[server]">
  <option name="port" type="int" default="8501"/>
  <option name="address" type="str" default="(unset)"/>
  <option name="baseUrlPath" type="str" default=""/>
  <option name="enableCORS" type="bool" default="true"/>
  <option name="enableXsrfProtection" type="bool" default="true"/>
  <option name="maxUploadSize" type="int" default="200">MB for file_uploader</option>
  <option name="maxMessageSize" type="int" default="200">MB for WebSocket</option>
  <option name="enableStaticServing" type="bool" default="false">Serve static/ directory</option>
  <option name="headless" type="bool" default="false"/>
  <option name="runOnSave" type="bool" default="false"/>
  <option name="fileWatcherType" type="str" default="auto" values="auto|watchdog|poll|none"/>
</section>

<section name="[browser]">
  <option name="serverAddress" type="str" default="localhost"/>
  <option name="serverPort" type="int" default="(same as server.port)"/>
  <option name="gatherUsageStats" type="bool" default="true"/>
</section>

<section name="[theme]">
  <option name="base" type="str" values="light|dark|path|url"/>
  <option name="primaryColor" type="str">CSS color</option>
  <option name="backgroundColor" type="str"/>
  <option name="secondaryBackgroundColor" type="str"/>
  <option name="textColor" type="str"/>
  <option name="font" type="str" values="sans-serif|serif|monospace|custom"/>
  <option name="baseFontSize" type="int" default="16"/>
  <option name="baseRadius" type="str" values="none|small|medium|large|full|10px"/>
</section>

</configuration>

<!-- ============================================================ -->
<!-- SECTION 8: DEPLOYMENT                                         -->
<!-- ============================================================ -->
<deployment>

<docker>
  <dockerfile>
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update &amp;&amp; apt-get install -y build-essential curl &amp;&amp; rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
  </dockerfile>
  <health_check>http://localhost:8501/_stcore/health</health_check>
</docker>

<community_cloud>
  <files>
    requirements.txt (pip dependencies)
    packages.txt (apt-get dependencies)
    .streamlit/config.toml (configuration)
  </files>
  <secrets>Settings > Secrets (paste TOML)</secrets>
  <limits>~1GB RAM, apps sleep after 12h</limits>
</community_cloud>

<nginx_reverse_proxy>
  <config>
location / {
    proxy_pass http://127.0.0.1:8501;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 86400;
}
  </config>
</nginx_reverse_proxy>

</deployment>

<!-- ============================================================ -->
<!-- SECTION 9: ARCHITECTURE PATTERNS                              -->
<!-- ============================================================ -->
<architecture>

<project_structure>
my_app/
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml  # gitignored
├── pages/
│   ├── 1_📊_Dashboard.py
│   └── 2_⚙️_Settings.py
├── components/
├── utils/
├── tests/
├── app.py
├── requirements.txt
└── Dockerfile
</project_structure>

<multipage method="st.navigation" recommended="true">
  <usage>
pg = st.navigation([
    st.Page("pages/dashboard.py", title="Dashboard", icon="📊"),
    st.Page("pages/settings.py", title="Settings", icon="⚙️"),
])
pg.run()
  </usage>
</multipage>

<multipage method="pages_directory">
  <naming>Number prefix orders: 1_, 2_. Emoji for icons. Underscores become spaces.</naming>
</multipage>

<session_state>
  <initialization>
if "key" not in st.session_state:
    st.session_state.key = default
# OR
st.session_state.setdefault("key", default)
  </initialization>
  <widget_binding>st.text_input("...", key="input_key")</widget_binding>
  <callbacks>
def on_change():
    st.session_state.result = process(st.session_state.input)
st.text_input("...", key="input", on_change=on_change)
  </callbacks>
</session_state>

<fragments>
  <signature>@st.fragment(run_every=None)</signature>
  <usage>
@st.fragment
def my_fragment():
    st.selectbox(...)  # Only this fragment reruns on change
    if st.button("Full rerun"):
        st.rerun()  # Full script
    if st.button("Fragment rerun"):
        st.rerun(scope="fragment")  # Fragment only

@st.fragment(run_every="5s")
def live_data():
    st.line_chart(fetch_live())  # Auto-refreshes
  </usage>
</fragments>

<testing framework="AppTest">
  <usage>
from streamlit.testing.v1 import AppTest

def test_app():
    at = AppTest.from_file("app.py").run()
    assert not at.exception
    at.button[0].click().run()
    at.text_input[0].input("value").run()
    assert "value" in at.markdown[0].value
  </usage>
</testing>

</architecture>

<!-- ============================================================ -->
<!-- SECTION 10: THIRD-PARTY COMPONENTS                            -->
<!-- ============================================================ -->
<third_party>

<component name="streamlit-aggrid">
  <install>pip install streamlit-aggrid</install>
  <import>from st_aggrid import AgGrid, GridOptionsBuilder</import>
  <usage>
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_selection('multiple', use_checkbox=True)
AgGrid(df, gridOptions=gb.build(), theme='streamlit')
  </usage>
</component>

<component name="streamlit-extras">
  <install>pip install streamlit-extras</install>
  <examples>
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_logo import add_logo
  </examples>
</component>

<component name="streamlit-option-menu">
  <install>pip install streamlit-option-menu</install>
  <import>from streamlit_option_menu import option_menu</import>
  <usage>
selected = option_menu("Menu", ["Home", "Settings"], icons=['house', 'gear'], orientation="horizontal")
  </usage>
</component>

<component name="streamlit-authenticator">
  <install>pip install streamlit-authenticator</install>
  <import>import streamlit_authenticator as stauth</import>
</component>

<component name="streamlit-drawable-canvas">
  <install>pip install streamlit-drawable-canvas</install>
  <import>from streamlit_drawable_canvas import st_canvas</import>
  <usage>
canvas = st_canvas(drawing_mode="freedraw", stroke_width=3, height=400)
if canvas.image_data is not None:
    st.image(canvas.image_data)
  </usage>
</component>

<component name="streamlit-lottie">
  <install>pip install streamlit-lottie</install>
  <import>from streamlit_lottie import st_lottie, st_lottie_spinner</import>
</component>

</third_party>

<!-- ============================================================ -->
<!-- SECTION 11: DEPRECATIONS AND VERSION INFO                     -->
<!-- ============================================================ -->
<version_info>
  <current>1.52.0</current>
  <date>December 3, 2025</date>
  <python>3.9 - 3.14</python>
  
  <deprecated>
    <item>use_container_width → width="stretch"</item>
    <item>add_rows() under review for removal</item>
    <item>st.bokeh_chart removed (use streamlit-bokeh)</item>
    <item>@st.experimental_fragment → @st.fragment</item>
    <item>@st.cache → @st.cache_data/@st.cache_resource</item>
  </deprecated>
  
  <new_1_52>
    st.datetime_input combined widget
    st.download_button callable
    st.chat_input audio support
    Keyboard shortcuts for buttons
    Python 3.14 support
  </new_1_52>
</version_info>

</streamlit_reference>
```

---

## QUICK REFERENCE: COMMON PATTERNS

### Widget with Callback
```python
def handle_change():
    st.session_state.result = process(st.session_state.input)

st.text_input("Input", key="input", on_change=handle_change)
```

### Cached Data Loading
```python
@st.cache_data(ttl="1h")
def load_data(url):
    return pd.read_csv(url)
```

### Cached Resource (Singleton)
```python
@st.cache_resource
def get_model():
    return load_model("path/to/model")
```

### Database Connection
```python
conn = st.connection("sql", type="sql")
df = conn.query("SELECT * FROM table", ttl="10m")
```

### Chat Interface
```python
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
```

### Multipage with Navigation
```python
pg = st.navigation([
    st.Page("home.py", title="Home", icon="🏠"),
    st.Page("settings.py", title="Settings", icon="⚙️"),
])
pg.run()
```

### Fragment for Partial Reruns
```python
@st.fragment
def live_widget():
    option = st.selectbox("Choose", ["A", "B"])  # Only this reruns
    st.write(f"Selected: {option}")
```

### Testing
```python
from streamlit.testing.v1 import AppTest

def test_app():
    at = AppTest.from_file("app.py").run()
    at.button[0].click().run()
    assert "expected" in at.markdown[0].value
```

---

**Sources**: docs.streamlit.io, GitHub streamlit/streamlit, PyPI streamlit changelog (Version 1.52.0, December 2025)