# Cincinnati-Reds-Hackathon-2025

By: Etienne Busnel, Nick McNulty, Naman Lakhani, Kenzo Valentin, and Andrew Pollack

READ WITH BETTER VISUALS HERE: https://fordhamsas.wixsite.com/website/post/forecasting-mlb-playing-time-cincinnati-reds-2025-hackathon

Introduction
Imagine offering a baseball fan the chance to build a starting rotation featuring Shohei Ohtani, Tyler Glasnow, Clayton Kershaw, Tony Gonsolin, and Dustin May. Most would jump at the opportunity—after all, this collection of talent includes Cy Young winners, solid backend options, and two-way superstars. And yet, despite assembling this dream rotation, the 2024 Los Angeles Dodgers found themselves in a nightmare scenario: every single one of these pitchers landed on the injured list.


And yet, they still won the World Series.


The Dodgers' success wasn’t just about having stars—it was about preparing for the inevitability that some of those stars wouldn’t be available. They stockpiled depth, ensuring that when injuries struck, they had enough quality arms to stay competitive. Their ability to account for playing time uncertainty proved just as valuable as the high-powered offense that carried them to a championship.


In Major League Baseball, the best ability is availability. Front offices don’t just need to know how good a player is -- they need to know how much they can realistically expect them to play. This analysis aims to tackle that challenge by forecasting playing time (plate appearances for hitters and batters faced for pitchers) for the 2024 season, providing a roster-agnostic look at how much teams can count on their players to take the field.


Feature Creation
Examining the distribution of plate appearances (PA) and batters faced (BF) from the 2021-2023 seasons reveals key trends in player usage. Both distributions show a significant spike at zero, representing depth players who only made brief appearances before returning to the bench or minors.


For plate appearances, the distribution remains relatively steady from 100 PA up to around 700. In contrast, batters faced saw a decline around the 300 bf mark, likely due to the different roles that starting and relief pitchers play.



Given the differences between batting and pitching projections, we developed separate models for each, using role-specific features. The individual predictions for batting and pitching were then combined to estimate a player's total playing time.


We selected the following features for each model:


Batting-Specific
Total PA: Number of plate appearances a player had in the past seasons.

Age: Players tend to regress with age.

Bats: Were they a lefty, righty or switch hitter.

OPS: OPS had the highest correlation with plate appearances of all the traditional slash line stats.

xwOBA: The WOBA value expected based on a batter's contact quality.

Average Lineup Position: Players batting higher in orders get more plate appearances.

Home Runs per Fly Ball Percentage: What percent of fly balls were home runs.

Line Drives Ratio: What percentage of hits were line drives.

Ground Ball Ratio: What percentage of hits were line drives.

Strikeout Rate

Walk Rate


Pitching-Specific
Total PA: Number of plate appearances a player had in the past seasons.

SP Percent: Percent of pitcher appearances where the pitcher started the game.

Zone Chase Percentage: What percent of pitches were either thrown in the strike zone or were chased by the batter.

Average BF Per Outing: How many batters did the pitcher face in an appearance on average.

wOBA: wOBA value earned by batters when facing the pitcher.

xwOBA: The wOBA value they were expected to earn.

In Play Ratio: What percent of pitches thrown were hit into play.

Hit Type Ratios What percent of hits were ground balls/fly balls/popups/line drives.

Strikeout Rate

Walk Rate

Batting Average Allowed (BAA)

WHIP

Average Fastball Velocity


For numerical features like OPS, we calculated a weighted average from the last three seasons to account for recent performance. We utilized the traditional baseball weights: 5 for last season, 3 for two years ago, and 2 for three years ago. This ensures that more recent data has a larger influence, reflecting the typical trajectory of player performance.

To prevent players with limited at-bats from disproportionately skewing data, we regressed every player's statistics towards the average for their position by the equivalent of 5 plate appearances. For instance, a player who had only a single plate appearance and a hit would see their OPS adjusted from 1.000 to approximately .800, bringing it in line with more realistic expectations based on their position's overall performance. A player with 600 plate appearances would see very little adjustment though.


For the modeling process, we selected a NetElasticCV model, given the small prediction sample size and the inherent randomness of baseball. After training the batting and pitching models, we got the following feature weights.

Batting Features Importance
Batting Features Importance
Pitching Feature Importance
Pitching Feature Importance
Results
Through our model we were able to predict the amount of plate appearances that each batter would have in 2024, as well as the amount of batters each pitcher would face. While some features were undeniably more important than others (i.e. Age, Average Lineup Position, SP Pct), each feature gives a better picture of each pitcher/batter's performance from 2021-23. Of course, the most important feature ended up being the total batters faced or plate appearances each player had in the given time frame.

Most players in the data set didn't get that much playing time in 2024 according to our model (~100 plate appearances or less for batters, ~60 batters faced or less for pitchers), which just goes to show how many players are competing for time at the major league level.


Over the course of a season, hundreds of players are constantly being sent up and down from the minor leagues to the majors or vice versa. Our model emphasizes how important it is that each player plays at a high level to continue to get reps. What surprised us most was how unimportant certain features were in the final models. For example, the ground ball ratio and strikeout rate for pitchers were not extremely important. Usually, a pitcher's performance or expected performance metrics are highly associated with their ability to strike batters out and/or induce weak hits to the ground that can easily be fielded. We included these metrics in our pitching model expecting them to be very important, but their importance coefficients were lower than the median value.


Future Areas to Consider
More seasons of data: Baseball's inherent randomness makes additional seasons crucial for accurately assessing player performance, identifying aging trends, and using a season as a validation set.

Injury data: Without specific injury history, the model can't fully account for the risk of injuries, which limits its ability to adjust projections for injury-prone players.

Minor league data: The model struggles to predict rookie performance, as it lacks insight into whether a late 2023 call-up is a top prospect or a temporary fill-in.

Fielding: The model does not account for defensive skills, which can influence playing time.

General aging trends: More data would improve the model's ability to capture and predict aging patterns for different player archetypes.


Appendix
Full Code: https://github.com/etienne-busnel/Cincinnati-Reds-Hackathon-2025/tree/main

