## openreview ratings vs citations
```
project
│   README.md
│   utils.py
│   Data_scrapping_Example.ipynb: data scrapping example
│   Parsing_pre-scrapped_data.ipynb: parsing pre-scrapped_data in repo/data folder
│
└───data
│   │
│   └───ICLR20**
│       │   preprocessed_table.pkl
│       │   google scholar citation info.json
│       │   openreview data.pkl or openreview data.hdf5
```


* A simple analysis comparing ICLR openreview official ratings and the number of citations of each accepted paper. 
* This repository contains:
	* openreview review lists, citation data of ICLR accepted papers
	* Data analysis codes & results


![citations_vs_ratings_17](https://raw.githubusercontent.com/isingmodel/openreview_ratings_vs_citations/master/figs/Log_Citation_vs_Review_Rating_ICLR_2017.png?raw=true)
![citations_vs_ratings_18](https://raw.githubusercontent.com/isingmodel/openreview_ratings_vs_citations/master/figs/Log_Citation_vs_Review_Rating_ICLR_2018.png?raw=true)
![citations_vs_ratings_19](https://raw.githubusercontent.com/isingmodel/openreview_ratings_vs_citations/master/figs/Log_Citation_vs_Review_Rating_ICLR_2019.png?raw=true)
![citations_vs_ratings_20](https://raw.githubusercontent.com/isingmodel/openreview_ratings_vs_citations/master/figs/Log_Citation_vs_Review_Rating_ICLR_2020.png?raw=true)




## TODO
* Data Analysis






## Trouble shooting
* If you cannot load pickle data files, update python or pandas version to read higher protocol version of pickle file. 


## Ideas
* Papers with an average rating of less than 6 may have to be excluded from the analysis because the intention of the Program Chairs is relatively reflected. (rating 6: marginally above the acceptance threshold)
* Some authors crave a quick response from reviewers.(i.e. https://openreview.net/forum?id=dIVrWHP9_1i ). The response time matters?
* Quite many papers rejected from ICLR are re-submited and accepted for ICML. What about them?
* The correlation between and Review ratings and the number of Citations decreased over time. why?
	* hypothesis 1: As the years passed, the number of submitted papers increased, and more reviewers had to participate in the review, reducing the quality of the reviewers.
	* hypothesis 2: As the years passed, the number of submitted papers increased, and the quality of reviews decreased as more reviews were required per reviewer.
	* hypothesis 3: Papers in the 2019 and 2020 have not yet been properly evaluated in terms of citations. More time is needed for the citation distribution to become clear.

## Other reference sites 
* https://horace.io/OpenReviewExplorer/ ( https://github.com/Chillee/OpenReviewExplorer )
* AN OPEN REVIEW OF OPENREVIEW: A CRITICAL ANALYSIS OF THE MACHINE LEARNING CONFERENCE REVIEW PROCESS https://openreview.net/forum?id=Cn706AbJaKW
* Dynamic patterns of open review process
https://www.sciencedirect.com/science/article/abs/pii/S0378437121005185

## Any idea & Qeustion? please write anything on github issues. 
