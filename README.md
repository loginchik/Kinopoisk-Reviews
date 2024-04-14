# Kinopoisk Reviews Scrapper 

Scrapper source code is here: [kinopoisk_reviews_scrapper.py](kinopoisk_reviews_scrapper.py)

Simple ui to use it is here: [main.ipynb](main.ipynb)

Scrapper gets link to movie. From main page it saves movie title, from reviews page gets all the reviews available 
there. 

Resulting data structure is:

| Column                  | Type | Description                                              | 
|-------------------------|------|----------------------------------------------------------|
| comment_id              | str  | Review unique ID                                         | 
| comment_date            | str  | Publication date and time in ISO format if possible      | 
| comment_link            | str  | URL to review                                            |
| comment_kind            | str  | positive / neutral / bad - Review mood defined by author | 
| comment_heading         | str  | Heading of review, may be empty                          | 
| comment_text            | str  | Review body text                                         | 
| comment_useful_positive | int  | Times other users marked the review as helpful           | 
| comment_useful_negative | int  | Times other users market the review as not helpful       | 
| movie_title             | str  | Reviewed movie title                                     | 
| movie_link              | str  | URL to reviewed movie                                    |

## Collected files

1. [File from 2024-04-14](data/kinopoisk_db_240414.csv) contains 3481 unique reviews for: История игрушек (1995), 
История игрушек 2 (1999), История игрушек: Большой побег (2010), История игрушек 4 (2019), Тачки (2006), Тачки 2 (2011), 
Тачки 3 (2017), Корпорация монстров (2001), Университет монстров (2013), ВАЛЛ·И (2008), Головоломка (2015), Душа (2020), 
Приключения Флика (1998), Тайна Коко (2017), Лука (2021), Я краснею (2022), Элементарно (2023), Суперсемейка (2004), 
Суперсемейка 2 (2018), Зверополис (2016), 101 далматинец (1961), Золушка (1949), Король Лев (1994), Дамбо (1941), 
Белоснежка и семь гномов (1937), Красавица и чудовище (1991), Мулан (1998), Кошмар перед Рождеством (1993) 
