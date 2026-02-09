the innovation-factory is a collection of interactive apps. The landing page is a gallery of tiles of existing projects and a tile to "build a new idea". The apps need to run locally before being deployed to a Databricks App. Running locally it should use a suitable postgres database. Deployed on Databricks, it should use the autoscaling Lakebase postgres database "innovation-factory" (find it in the specified workspace profile via APX. In the database a suitable layout to have multiple projects exist side by side (incl. all components like mock up data, users, etc).

Take the code for the vi-home-one and bsh-home-connect app located in @/Users/felix.mutzl/Databricks Git/vi-home-one and @/Users/felix.mutzl/Databricks Git/bsh-home-connect and integrate it into the innovation-factory. Copy over the code artefacts of frontend and backend that are required and integrate it into the innovation-factory. 

The "build a new idea" exposes a chat interface with a chatbot behind that asks the user the following questions and then compiles the initial prompt for a coding agent: 1) what's the name of the company? It can also be made up. 2) Describe what you'd like to build next.

leverage databricks ai-dev-kit to build with deployment on Databricks in mind (esp. as a Databricks app w APX)

create a new repo in the link git account called innovation-factory and commit + push changes there onto the main branch for now
