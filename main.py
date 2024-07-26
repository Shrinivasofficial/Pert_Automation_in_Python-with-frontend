import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import networkx as nx

st.set_page_config(
    page_title="Streamlit Expanded Layout",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'tasks_data' not in st.session_state:
    st.session_state['tasks_data'] = []

if 'num_tasks' not in st.session_state:
    st.session_state['num_tasks'] = 0

if 'project_title_submitted' not in st.session_state:
    st.session_state['project_title_submitted'] = False

if 'tasks_submitted' not in st.session_state:
    st.session_state['tasks_submitted'] = False

st.sidebar.title("Navigation")
selection = st.sidebar.selectbox("Go to", ["Home", "PERT", "CPM", "Table"])

if selection == 'PERT':
    st.title('PERT Automation')

    # Project title input
    st.image("venv/e282fdd4-project-plan.jpg", caption="Project Planning Image")

    project_title = st.text_input("Name of your project: ")

    if project_title and not st.session_state['project_title_submitted']:
        if st.button("Submit Project Title"):
            st.session_state['project_title_submitted'] = True

    if st.session_state['project_title_submitted']:
        # Number of tasks input
        num_tasks = st.number_input("Enter the number of tasks:", min_value=1, value=1, key='num_tasks_input')

        if st.button("Submit Task Number"):
            st.session_state['num_tasks'] = num_tasks

        if st.session_state['num_tasks'] > 0:
            with st.form("task_form"):
                for i in range(st.session_state['num_tasks']):
                    st.subheader(f"Task {i + 1}")
                    task_name = st.text_input(f"Enter the name for Task {i + 1}:", key=f'task_name_{i}')
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        optimistic = st.number_input(f"Optimistic time", min_value=0, value=0, key=f'optimistic_{i}')
                    with col2:
                        most_likely = st.number_input(f"Most likely time", min_value=0, value=0, key=f'most_likely_{i}')
                    with col3:
                        pessimistic = st.number_input(f"Pessimistic time", min_value=0, value=0, key=f'pessimistic_{i}')
                    predecessors = st.text_input(f"Predecessors (comma-separated):", key=f'predecessors_{i}')

                submitted = st.form_submit_button("Submit Tasks")

                if submitted:
                    tasks_data = []
                    for i in range(st.session_state['num_tasks']):
                        task_name = st.session_state[f'task_name_{i}']
                        optimistic = st.session_state[f'optimistic_{i}']
                        most_likely = st.session_state[f'most_likely_{i}']
                        pessimistic = st.session_state[f'pessimistic_{i}']
                        predecessors = st.session_state[f'predecessors_{i}'].split(',')

                        if task_name and optimistic and most_likely and pessimistic:
                            expected_duration = (optimistic + 4 * most_likely + pessimistic) / 6
                            tasks_data.append({
                                "Task Name": task_name,
                                "Optimistic": optimistic,
                                "Most Likely": most_likely,
                                "Pessimistic": pessimistic,
                                "Expected Duration": expected_duration,
                                "Predecessors": [p.strip() for p in predecessors if p.strip()]  # Clean up predecessor inputs
                            })

                    st.session_state['tasks_data'] = tasks_data
                    st.session_state['tasks_submitted'] = True

    if st.session_state['tasks_submitted']:
        df = pd.DataFrame(st.session_state['tasks_data'])
        st.subheader("Tasks Data")
        st.dataframe(df)

elif selection == 'Home':
    st.title("IT Project Management Automation")

elif selection == 'CPM':
    st.title("CPM Automation")

elif selection == 'Table':
    st.title("Expected Duration")
    if st.session_state['tasks_submitted']:
        df = pd.DataFrame(st.session_state['tasks_data'])
        st.subheader("Tasks Data")
        st.dataframe(df)

        # Forward and Backward Pass Calculations
        tasks = st.session_state['tasks_data']
        task_names = [task["Task Name"] for task in tasks]
        task_durations = {task["Task Name"]: task["Expected Duration"] for task in tasks}
        predecessors = {task["Task Name"]: task["Predecessors"] for task in tasks}

        # Initialize start and finish times
        ES = {task: 0 for task in task_names}
        EF = {task: task_durations[task] for task in task_names}
        LS = {task: float('inf') for task in task_names}
        LF = {task: float('inf') for task in task_names}

        # Calculate ES and EF
        for task in task_names:
            if predecessors[task]:
                ES[task] = max(EF[pred] for pred in predecessors[task])
            EF[task] = ES[task] + task_durations[task]

        project_duration = max(EF.values())

        # Calculate LF and LS
        for task in task_names:
            LF[task] = project_duration

        for task in reversed(task_names):
            successors = [succ for succ in task_names if task in predecessors[succ]]
            if successors:
                LF[task] = min(LS[succ] for succ in successors)
            LS[task] = LF[task] - task_durations[task]

        st.subheader("Forward and Backward Pass Results")
        st.write(f"Project Duration: {project_duration}")

        results = []
        for task in task_names:
            results.append({
                "Task Name": task,
                "ES": ES[task],
                "EF": EF[task],
                "LS": LS[task],
                "LF": LF[task],
                "Slack": LS[task] - ES[task]
            })

        results_df = pd.DataFrame(results)
        st.dataframe(results_df)

        # Plotting the graph using Plotly
        G = nx.DiGraph()

        for task in tasks:
            G.add_node(task["Task Name"], duration=task["Expected Duration"], ES=ES[task["Task Name"]], EF=EF[task["Task Name"]], LS=LS[task["Task Name"]], LF=LF[task["Task Name"]])
            for pred in task["Predecessors"]:
                G.add_edge(pred, task["Task Name"])

        pos = nx.spring_layout(G)
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.append(x0)
            edge_x.append(x1)
            edge_x.append(None)
            edge_y.append(y0)
            edge_y.append(y1)
            edge_y.append(None)

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )

        node_x = []
        node_y = []
        node_text = []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(f"{node}<br>ES: {G.nodes[node]['ES']}<br>EF: {G.nodes[node]['EF']}<br>LS: {G.nodes[node]['LS']}<br>LF: {G.nodes[node]['LF']}")

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_text,
            textposition="top center",
            hoverinfo='text',
            marker=dict(
                color='LightSkyBlue',
                size=10,
                line_width=2
            )
        )

        fig = go.Figure(data=[edge_trace, node_trace],
                        layout=go.Layout(
                            title='Project Graph',
                            showlegend=False,
                            hovermode='closest',
                            margin=dict(b=0, l=0, r=0, t=40),
                            xaxis=dict(showgrid=False, zeroline=False),
                            yaxis=dict(showgrid=False, zeroline=False)
                        ))

        st.plotly_chart(fig)
