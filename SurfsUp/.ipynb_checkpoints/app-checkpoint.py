# Import the dependencies.
import numpy as np
import pandas as pd

from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session



#################################################
# Database Setup
#################################################


# reflect an existing database into a new model
engine = create_engine("sqlite:///Resources/hawaii.sqlite")


# reflect the tables
Base = automap_base()
Base.prepare(autoload_with=engine)
print(Base.classes.keys())


# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################
@app.route("/")
def home():
    """List all available API routes."""
    return (
        f"Welcome to the Hawaii Climate API! It's your vacation destination information situation.<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation - Last 12 Months of Precipitation Data<br/>"
        f"/api/v1.0/stations - List of Stations<br/>"
        f"/api/v1.0/tobs - Last 12 Months of Temperature Observations for Most Active Station<br/>"
        f"/api/v1.0/temp/start/end - Min, Max, and Avg Temperature for a Given Date Range<br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the last 12 months of precipitation data as JSON."""
    latest_date = session.query(func.max(Measurement.date)).scalar()
    latest_date = pd.to_datetime(latest_date)
    one_year_ago = latest_date - pd.DateOffset(years=1)

    # Query precipitation data
    precip_data = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year_ago.date()).all()

    # Convert to dictionary
    precip_dict = {date: prcp for date, prcp in precip_data}
    
    return jsonify(precip_dict)

@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of all stations."""
    station_data = session.query(Station.station).all()
    station_list = [station[0] for station in station_data]

    return jsonify(station_list)


@app.route("/api/v1.0/tobs")
def temperature_obs():
    """Return temperature observations for the most active station for the last 12 months."""
    # Find the most active station
    most_active_station = session.query(Measurement.station).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()[0]

    # Find the most recent date
    latest_date = session.query(func.max(Measurement.date)).scalar()
    latest_date = pd.to_datetime(latest_date)
    one_year_ago = latest_date - pd.DateOffset(years=1)

    # Query temperature observations
    temp_data = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station).\
        filter(Measurement.date >= one_year_ago.date()).all()

    # Convert to list of dictionaries
    temp_list = [{"date": date, "temperature": tobs} for date, tobs in temp_data]

    return jsonify(temp_list)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temp_stats(start, end=None):
    """Return min, max, and avg temperature for a given date range."""
    # Base query
    query = session.query(
        func.min(Measurement.tobs),
        func.max(Measurement.tobs),
        func.avg(Measurement.tobs)
    ).filter(Measurement.date >= start)

    # If an end date is provided, filter by it
    if end:
        query = query.filter(Measurement.date <= end)

    temp_stats = query.all()

    return jsonify({
        "Start Date": start,
        "End Date": end if end else "Latest Available",
        "Min Temp": temp_stats[0][0],
        "Max Temp": temp_stats[0][1],
        "Avg Temp": round(temp_stats[0][2], 2)
    })



# Run the app
if __name__ == "__main__":
    app.run(debug=True)