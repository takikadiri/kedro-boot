import pandas as pd
from pathlib import Path
import streamlit as st
from kedro_boot.app.booter import boot_project, boot_package


@st.cache_resource
def get_kedro_boot_session(boot_type):
    if boot_type == "project":
        return boot_project(
            project_path=Path.cwd(), kedro_args={"pipeline": "__default__"}
        )
    else:
        return boot_package(
            package_name="spaceflights",
            kedro_args={"pipeline": "__default__", "conf_source": "conf"},
        )


# get kedro boot session before first form submit (first run)
get_kedro_boot_session("project")

st.title("Spaceflights shuttle price prediction")

with st.container():
    with st.form("my_form"):
        st.write("Shuttle Price Prediction")
        shuttle = {
            "engines": st.slider("engines", 0, 12, 2),
            "passenger_capacity": st.slider("passenger_capacity", 1, 20, 5),
            "crew": st.slider("crew", 0, 20, 5),
            "d_check_complete": st.checkbox("d_check_complete"),
            "moon_clearance_complete": st.checkbox("moon_clearance_complete"),
            "iata_approved": st.checkbox("iata_approved"),
            "company_rating": st.slider("company_rating", 0.0, 1.0, 0.95),
            "review_scores_rating": st.slider("review_score_rating", 20, 100, 88),
        }

        submitted = st.form_submit_button("Predict Price")

if submitted:
    shuttle_df = pd.DataFrame(shuttle, index=[0])
    shuttle_price = get_kedro_boot_session("project").run(
        namespace="inference", inputs={"features_store": shuttle_df}
    )
    formated_shuttle_price = round(shuttle_price[0], 3)

    st.success(f"The predicted shuttle price is {formated_shuttle_price} $")
