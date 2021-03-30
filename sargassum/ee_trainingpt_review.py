#!/usr/bin/env python
# coding: utf-8

# ## Review Training point band statistics, correlations for final band selection

# In[1]:


# Import GEE & initialize
import ee
# Trigger the authentication flow. 
# -- I think this was a onetime thing, but keeping here in case
# ee.Authenticate()
# Initialize the library.
ee.Initialize()
import geemap


# In[2]:


# Import Libraries
import os
import pandas as pd
import geopandas as gpd
import numpy as np
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt


# In[3]:


samples_ee = ee.FeatureCollection("projects/ee-abnatcap/assets/sargassum/samples20190507_allbands")
print("Column names: ", samples_ee.first().propertyNames().getInfo())
print('Count: ', samples_ee.size().getInfo())


# In[4]:


# samples_geojson = geemap.ee_to_geojson(samples_ee)
#  Doesn't work -- got error: Collection query aborted after accumulating over 5000 elements.


# In[5]:


samples_geojson = '/Users/arbailey/Google Drive File Stream/My Drive/geeout/samples20190507_allbands.geojson'
samples_gdf = gpd.read_file(samples_geojson)
print(samples_gdf.crs)
print(samples_gdf.columns)
samples_gdf


# In[6]:


fig = px.scatter_matrix(samples_gdf,
    dimensions=["AFAI", "FAI", "SAVI", "SEI", "NDVI"],
    color="lc_code")
fig.update_traces(diagonal_visible=False)
fig.show()


# In[7]:


fig = px.scatter_matrix(samples_gdf,
    dimensions=['AFAI', 'FAI', 'SAVI', 'SEI', 'NDVI', 'NDVI_max', 'NDVI_mean', 'NDVI_median', 'NDVI_min', 'NDVI_stdDev'],
    color = 'lc_code')
fig.update_traces(diagonal_visible=False)
fig.show()


# In[8]:


fig = px.scatter_matrix(samples_gdf,
    dimensions=['NDVI', 'NDVI_max', 'NDVI_mean', 'NDVI_median', 'NDVI_min', 'NDVI_stdDev'] ,
    color = 'lc_code')
fig.update_traces(diagonal_visible=False)
fig.show()


# In[9]:


fig = px.scatter_matrix(samples_gdf,
    dimensions=['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8','B8A', 'B11', 'B12'],
    color ='lc_code')
fig.update_traces(diagonal_visible=False)
fig.show()


# In[10]:


fig = px.scatter_matrix(samples_gdf,
    dimensions=[ 'B11', 'B12'],
    color ='lc_code')
fig.update_traces(diagonal_visible=False)
fig.show()


# In[11]:


fig = px.scatter_matrix(samples_gdf,
    dimensions=['B5', 'B6', 'B7', 'B8','B8A'],
    color = 'lc_code')
fig.update_traces(diagonal_visible=False)
fig.show()


# In[12]:


fig = px.scatter_matrix(samples_gdf,
    dimensions=['FAI', 'NDVI'],
    color = 'lc_code')
fig.update_traces(diagonal_visible=False)
fig.show()


# In[13]:


fig = px.scatter_matrix(samples_gdf,
    dimensions=['NDVI','SEI'],
    color = 'lc_code')
fig.update_traces(diagonal_visible=False)
fig.show()


# In[14]:


fig = px.scatter_matrix(samples_gdf,
    dimensions=['B8','B8A'],
    color = 'lc_code')
fig.update_traces(diagonal_visible=False)
fig.show()


# In[15]:


allbands_pluslc = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8','B8A', 'B11', 'B12', 'AFAI', 'FAI', 'NDVI', 'NDVI_max', 'NDVI_mean', 'NDVI_median','NDVI_min', 'NDVI_stdDev', 'NDVI_dmed', 'SAVI', 'SEI', 'lc_code']
samples_pluslc_df = samples_gdf[allbands_pluslc]
samples_pluslc_df


# In[16]:


allbands_nolc = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8','B8A', 'B11', 'B12', 'AFAI', 'FAI', 'NDVI', 'NDVI_max', 'NDVI_mean', 'NDVI_median','NDVI_min', 'NDVI_stdDev', 'NDVI_dmed', 'SAVI', 'SEI']
samples_nolc_df = samples_gdf[allbands_nolc]
samples_nolc_df


# In[17]:


bands_lowcorr = ['B2','B5','B8A','B12','FAI','SEI', 'NDVI','NDVI_median','NDVI_min']
bands_lowcorr = ['B2','B5','B8','B8A','B12','FAI','SEI', 'NDVI','NDVI_median','NDVI_min','NDVI_dmed']


# In[18]:


fig = px.scatter_matrix(samples_gdf,
    dimensions=bands_lowcorr,
    color = 'lc_code')
fig.update_traces(diagonal_visible=False)
fig.show()


# In[19]:


# https://heartbeat.fritz.ai/seaborn-heatmaps-13-ways-to-customize-correlation-matrix-visualizations-f1c49c816f07
# https://seaborn.pydata.org/examples/many_pairwise_correlations.html
matrix = np.triu(samples_nolc_df.corr())
sns.heatmap(samples_nolc_df.corr(), annot=True, mask=matrix)


# In[20]:


# Correlation matrix for ALL land cover classes together
mask = np.triu(samples_nolc_df.corr()) # use to block out top half of matrix viz
cmap = sns.diverging_palette(220, 20, as_cmap=True)
f, ax = plt.subplots(figsize=(20, 14))
sns.heatmap(samples_nolc_df.corr(), annot=True, mask=mask, square=True, cmap='vlag', vmin=-1, vmax=1, center= 0, fmt='.1g')


# In[21]:


f, ax = plt.subplots(figsize=(20, 14))
sns.heatmap(samples_nolc_df.corr(), annot=True, square=True, cmap='vlag', vmin=-1, vmax=1, center= 0)
ax.set_title('All Bands, All Classes - ' + str(len(samples_gdf)) + ' samples')


# In[22]:


f, ax = plt.subplots(figsize=(20, 14))
samples_sarg_df = samples_gdf.loc[samples_gdf["lc_code"] == 0,allbands_nolc]
sns.heatmap(samples_sarg_df.corr(), annot=True, square=True, cmap='vlag', vmin=-1, vmax=1, center= 0)
ax.set_title('Sargassum - ' + str(len(samples_sarg_df)) + ' samples')


# In[23]:


f, ax = plt.subplots(figsize=(20, 14))
samples_lowcorr_gdf = samples_gdf[bands_lowcorr]
sns.heatmap(samples_lowcorr_gdf.corr(), annot=True, square=True, cmap='vlag', vmin=-1, vmax=1, center= 0)
ax.set_title('All Classes - ' + str(len(samples_gdf)) + ' samples')


# In[24]:


samples_sarg_df = samples_gdf.loc[samples_gdf["lc_code"] == 0, bands_lowcorr]
f, ax = plt.subplots(figsize=(20, 14))
sns.heatmap(samples_sarg_df.corr(), annot=True, square=True, cmap='vlag', vmin=-1, vmax=1, center= 0)
ax.set_title('Sargassum - ' + str(len(samples_sarg_df)) + ' samples')


# In[25]:


samples_cloud_df = samples_gdf.loc[samples_gdf["lc_code"] == 4, bands_lowcorr]
f, ax = plt.subplots(figsize=(20, 14))
sns.heatmap(samples_cloud_df.corr(), annot=True, square=True, cmap='vlag', vmin=-1, vmax=1, center= 0)
ax.set_title('Clouds - ' + str(len(samples_cloud_df)) + ' samples')


# In[26]:


samples_otherveg_df = samples_gdf.loc[samples_gdf["lc_code"] == 1, bands_lowcorr]
f, ax = plt.subplots(figsize=(20, 14))
sns.heatmap(samples_otherveg_df.corr(), annot=True, square=True, cmap='vlag', vmin=-1, vmax=1, center= 0)
ax.set_title('Other Veg - ' + str(len(samples_otherveg_df)) + ' samples')


# In[27]:


samples_beach_df = samples_gdf.loc[samples_gdf["lc_code"] == 2, bands_lowcorr]
f, ax = plt.subplots(figsize=(20, 14))
sns.heatmap(samples_beach_df.corr(), annot=True, square=True, cmap='vlag', vmin=-1, vmax=1, center= 0)
ax.set_title('Beach - ' + str(len(samples_beach_df)) + ' samples')


# In[28]:


samples_building_df = samples_gdf.loc[samples_gdf["lc_code"] == 3, bands_lowcorr]
f, ax = plt.subplots(figsize=(20, 14))
sns.heatmap(samples_building_df.corr(), annot=True, square=True, cmap='vlag', vmin=-1, vmax=1, center= 0)
ax.set_title('Buildings - ' + str(len(samples_building_df)) + ' samples')


# In[29]:


bands_lowcorr_lc = bands_lowcorr + ['lc_code']
print(bands_lowcorr_lc)
samples_lowcorr_lc_df = samples_gdf[bands_lowcorr_lc]
samples_lowcorr_lc_df


# In[30]:


# Reshape data frame to a normalized format for bands/indices
samples_lowcorr_lc_norm_df = samples_lowcorr_lc_df.melt(id_vars=['lc_code'], value_vars=bands_lowcorr,
    var_name='band_index', value_name='value')
conditions = [
    (samples_lowcorr_lc_norm_df['lc_code'] == 0),
    (samples_lowcorr_lc_norm_df['lc_code'] == 1),
    (samples_lowcorr_lc_norm_df['lc_code'] == 2),
    (samples_lowcorr_lc_norm_df['lc_code'] == 3),
    (samples_lowcorr_lc_norm_df['lc_code'] == 4),
    ]
lc_names = ['sargassum', 'other veg', 'beach', 'buildings', 'clouds']
samples_lowcorr_lc_norm_df['lc'] = np.select(conditions, lc_names)
samples_lowcorr_lc_norm_df


# In[31]:


px.scatter(
    samples_lowcorr_lc_norm_df, x='band_index', y='value', color='lc', 
    title='Reflectance / Value by Band and Land Cover',
    labels=dict(
       band_index='Band or Index', 
       value='Reflectance or Value')
)


# In[32]:


# Grouped boxplot
# All Land Cover classes
sns.set_style("whitegrid")
sns.set_context("notebook", font_scale=2, rc={"lines.linewidth": 1})
my_pal = {"sargassum": "gold", "other veg": "limegreen", "beach":"beige", 'buildings':'brown', 'clouds':'lightgrey'}
f, ax = plt.subplots(figsize=(24, 12))
sns.boxplot(x='band_index', y='value', hue='lc', data=samples_lowcorr_lc_norm_df, palette=my_pal)


# In[33]:


f, ax = plt.subplots(figsize=(24, 12))
sns.stripplot(x="band_index", y="value", hue="lc", data=samples_lowcorr_lc_norm_df, palette=my_pal, dodge=True)


# In[34]:


sns.set_context("notebook", font_scale=1.2, rc={"lines.linewidth": 1})
f, ax = plt.subplots(figsize=(10, 10))
plt.ylim(-1, 1)
sns.boxplot(x='band_index', y='value', hue='lc', data=samples_lowcorr_lc_norm_df[samples_lowcorr_lc_norm_df["lc_code"] == 0], palette=my_pal)


# In[35]:


f, ax = plt.subplots(figsize=(10, 10))
plt.ylim(-1, 1)
sns.boxplot(x='band_index', y='value', hue='lc', data=samples_lowcorr_lc_norm_df[samples_lowcorr_lc_norm_df["lc_code"] == 1], palette=my_pal)


# In[36]:


f, ax = plt.subplots(figsize=(10, 10))
plt.ylim(-1, 1)
sns.boxplot(x='band_index', y='value', hue='lc', data=samples_lowcorr_lc_norm_df[samples_lowcorr_lc_norm_df["lc_code"] == 2], palette=my_pal)


# In[37]:


f, ax = plt.subplots(figsize=(10, 10))
plt.ylim(-1, 1)
sns.boxplot(x='band_index', y='value', hue='lc', data=samples_lowcorr_lc_norm_df[samples_lowcorr_lc_norm_df["lc_code"] == 3], palette=my_pal)


# In[38]:


f, ax = plt.subplots(figsize=(10, 10))
plt.ylim(-1, 1)
sns.boxplot(x='band_index', y='value', hue='lc', data=samples_lowcorr_lc_norm_df[samples_lowcorr_lc_norm_df["lc_code"] == 4], palette=my_pal)


# In[ ]:




