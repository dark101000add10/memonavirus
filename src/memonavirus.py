import sys
import datetime
import logging
import praw
import json
import github
import typing
import random

from praw import models

logger = logging.getLogger(__name__)
handler = logging.FileHandler('../logs/{}.log'.format(str(datetime.datetime.now()).replace(' ', '_').replace(':', 'h', 1).replace(':', 'm').split('.')[0][:-2]))
formatter = logging.Formatter('%(asctime)s::%(levelname)s::%(name)s::%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)

with open('creds.json', 'r') as fp:
    credentials = json.load(fp)

logger.info("Authenticating with Reddit...")
_reddit = praw.Reddit(
    client_id=credentials["CLIENT_ID"],
    client_secret=credentials["CLIENT_SECRET"],
    user_agent=credentials["CLIENT_AGENT"],
    username=credentials["CLIENT_USERNAME"],
    password=credentials["CLIENT_PASSWORD"]
)
try:
    if _reddit.user.me().name != credentials["CLIENT_USERNAME"]:
        raise AssertionError("Authenticated unexpectedly!")
except Exception as ex:
    logger.error("Authentication failed. Check the password, ID, or secret. Goodbye...")
    logger.debug("Clearing presence...")
    raise ex
logger.info("Authenticated as {}".format(_reddit.user.me().name))

logger.info("Authenticating with Github...")
_github = github.Github(credentials["GITHUB_TOKEN"])
_repo = _github.get_repo("dovedevic/memonavirus")
logger.info("Authenticated as {} into {}".format(_github.get_user().name, _repo.full_name))

# Variables
logger.info("Setting up variables and environment...")
_hour = datetime.datetime.today().hour
_debug = True
_commentlog = open("../data/memes_comments.{}.{}.log".format(datetime.datetime.today().day, datetime.datetime.today().hour), "a")
_infectionlog = open("../data/memes_infections.{}.{}.log".format(datetime.datetime.today().day, datetime.datetime.today().hour), "a")
logger.info("Finished setting up.")
# End Variables


def on_comment(comment: models.Comment):
    try:
        parent = comment.parent()
        if type(parent) is models.Comment:
            # Did an uninfected person reply to an infected persons comment?
            if parent.author_flair_text and "INFECTED" in parent.author_flair_text and ((comment.author_flair_text and "INFECTED" not in comment.author_flair_text) or not comment.author_flair_text):
                # infection!
                infect(comment, parent)
        else:  # if type(parent) is models.Submission
            # Did an uninfected person reply to an infected persons submission? Roll dice for a 1 in 100
            if parent.author_flair_text and "INFECTED" in parent.author_flair_text and ((comment.author_flair_text and "INFECTED" not in comment.author_flair_text) or not comment.author_flair_text) and random.randint(1, 100) == 69:
                infect(comment, parent)
        # if _debug:
        #     print(comment)
        # TSV Format: Timestamp, Commentor Name, Commentor Comment ID, Commented on User, Commented on Item ID, Item Type, Commented on ?Infected? User
        _commentlog.write("{}\tu/{}\t{}\tu/{}\t{}\t{}\t{}\n".format(
            str(datetime.datetime.now()),
            comment.author.name,
            comment.id,
            "deleted" if not parent.author else parent.author.name,
            parent.id,
            "C" if type(parent) is models.Comment else "S",
            "I" if (parent.author_flair_text and "INFECTED" in parent.author_flair_text) else "N"
        ))
    except Exception as ex:
        logger.info("ERROR IN ON_COMMENT")
        logger.info(str(ex))
        pass


def infect(comment: models.Comment, infected_by: typing.Union[models.Comment, models.Submission]):
    try:
        logger.info("Beginning to infect redditor u/{} because of the {} by u/{}".format(
            comment.author.name,
            "comment" if type(infected_by) is models.Comment else "submission",
            "deleted" if not infected_by.author else infected_by.author.name
        ))
        # TSV Format: Timestamp, Contractor Name, Contractor Comment ID, Commented on User, Commented on Item, Item Type
        _infectionlog.write("{}\tu/{}\t{}\tu/{}\t{}\t{}\n".format(
            str(datetime.datetime.now()),
            comment.author.name,
            comment.id,
            "deleted" if not infected_by.author else infected_by.author.name,
            infected_by.id,
            "C" if type(infected_by) is models.Comment else "S"
        ))

        # if not self._debug:
        #     infected_by.subreddit.flair.set(comment.author, flair_template_id='0e8e4996-604b-11ea-bd19-0eedcb93a73d')
        #     await self._channel.send("☣ Redditor u/{} was infected because of the {} by u/{}".format(
        #         comment.author.name,
        #         "comment" if type(infected_by) is models.Comment else "submission",
        #         "deleted" if not infected_by.author else infected_by.author.name
        #     ))
        #     comment.author.message(
        #         "☣ You were infected by the r/memes Memonavirus ☣",
        #         "Hey u/{},\n\nYou contracted the r/memes Memonavirus from u/{}! You contracted it because you commented on their {}, [linked here](https://www.reddit.com{}).\n\n## Don't know what this is about?\n\n[Check out this announcement to see what this is about!](https://www.reddit.com/r/memes/comments/cu5ep9/community_awards_yes_please/)".
        #         format(
        #             comment.author.name,
        #             infected_by.author.name,
        #             "comment" if type(infected_by) is models.Comment else "submission",
        #             infected_by.permalink
        #         )
        #     )

    except Exception as ex:
        logger.info("ERROR IN INFECT")
        logger.info(str(ex))
        pass


def save_data_new_hour(force=False):
    global _hour, _commentlog, _infectionlog
    today = datetime.datetime.today()
    if today.hour != _hour or force:
        logger.info("Data files are being saved...")
        _hour = today.hour

        _commentlog.flush()
        repo_cmnt_filename = _commentlog.name
        _commentlog.close()
        _commentlog = open("../data/memes_comments.{}.{}.log".format(today.day, today.hour), "a")

        _infectionlog.flush()
        repo_infc_filename = _infectionlog.name
        _infectionlog.close()
        _infectionlog = open("../data/memes_infections.{}.{}.log".format(today.day, today.hour), "a")

        logger.info("Data files are saved. Uploading...")
        with open("../data/{}".format(repo_cmnt_filename), 'r') as fp:
            _repo.create_file(
                "data/{}".format(repo_cmnt_filename),
                "day {} hour {} automated hourly comment update".format(repo_cmnt_filename.split('.')[1], repo_cmnt_filename.split('.')[2]),
                fp.read()
            )
        with open("../data/{}".format(repo_infc_filename), 'r') as fp:
            _repo.create_file(
                "data/{}".format(repo_infc_filename),
                "day {} hour {} automated hourly infection  update".format(repo_infc_filename.split('.')[1], repo_infc_filename.split('.')[2]),
                fp.read()
            )

        logger.info("Done. `{}.{}` dataset is now live".format(today.day, today.hour))


logger.info("Starting comment streams...")

while True:
    try:
        for cmt in _reddit.subreddit('memes').stream.comments(skip_existing=True):
            on_comment(cmt)
            save_data_new_hour()
    except Exception as ex:
        logging.info("An error occurred in the comment thread. It was:\n{}".format(str(ex)))

# We should never get here...

































"""
class MemonavirusManager:
    Memonavirus Event Manager :: Integrated with discord.py and praw
    def __init__(self, bot, reddit, channel, git, debug):
        self._reddit = reddit
        self._bot = bot
        self._channel = bot.get_channel(channel)
        self._github = git
        self._debug = debug
        today = datetime.datetime.today()
        self._hour = today.hour
        self._lock = False
        self._commentlog = open("data/memes_comments.{}.{}.log".format(today.day, today.hour), "a")
        self._infectionlog = open("data/memes_infections.{}.{}.log".format(today.day, today.hour), "a")

    def save_data_new_hour(self, force=False):
        today = datetime.datetime.today()
        if today.hour != self._hour or force:
            logger.info("Data files are being saved...")
            self._hour = today.hour
            self._lock = True
            self._commentlog.flush()
            self._commentlog.close()
            self._commentlog = open("data/memes_comments.{}.{}.log".format(today.day, today.hour), "a")
            self._infectionlog.flush()
            self._infectionlog.close()
            self._infectionlog = open("data/memes_infections.{}.{}.log".format(today.day, today.hour), "a")
            self._lock = False

            logger.info("Done. `{}.{}` dataset is now live".format(today.day, today.hour))

    async def wait_for_lock(self):
        while self._lock:
            asyncio.sleep(0.1)

    async def on_comment(self, comment: models.Comment):
        try:
            parent = comment.parent()
            if type(parent) is models.Comment:
                # Did an uninfected person reply to an infected persons comment?
                if parent.author_flair_text and "INFECTED" in parent.author_flair_text and ((comment.author_flair_text and "INFECTED" not in comment.author_flair_text) or not comment.author_flair_text):
                    # infection!
                    await self.infect(comment, parent)
            else:  # if type(parent) is models.Submission
                # Did an uninfected person reply to an infected persons submission? Roll dice for a 1 in 100
                if parent.author_flair_text and "INFECTED" in parent.author_flair_text and ((comment.author_flair_text and "INFECTED" not in comment.author_flair_text) or not comment.author_flair_text) and random.randint(1, 100) == 69:
                    await self.infect(comment, parent)
            if self._debug:
                print(comment)
            # TSV Format: Timestamp, Commentor Name, Commentor Comment ID, Commented on User, Commented on Item ID, Item Type, Commented on ?Infected? User
            await self.wait_for_lock()
            self._commentlog.write("{}\tu/{}\t{}\tu/{}\t{}\t{}\t{}\n".format(
                str(datetime.datetime.now()),
                comment.author.name,
                comment.id,
                "deleted" if not parent.author else parent.author.name,
                parent.id,
                "C" if type(parent) is models.Comment else "S",
                "I" if (parent.author_flair_text and "INFECTED" in parent.author_flair_text) else "N"
            ))
        except Exception as ex:
            logger.info("ERROR IN ON_COMMENT")
            logger.info(str(ex))
            pass

    async def infect(self, comment: models.Comment, infected_by: typing.Union[models.Comment, models.Submission]):
        try:
            logger.info("Beginning to infect redditor u/{} because of the {} by u/{}".format(
                comment.author.name,
                "comment" if type(infected_by) is models.Comment else "submission",
                "deleted" if not infected_by.author else infected_by.author.name
            ))
            # TSV Format: Timestamp, Contractor Name, Contractor Comment ID, Commented on User, Commented on Item, Item Type
            await self.wait_for_lock()
            self._infectionlog.write("{}\tu/{}\t{}\tu/{}\t{}\t{}\n".format(
                str(datetime.datetime.now()),
                comment.author.name,
                comment.id,
                "deleted" if not infected_by.author else infected_by.author.name,
                infected_by.id,
                "C" if type(infected_by) is models.Comment else "S"
            ))

            # if not self._debug:
            #     infected_by.subreddit.flair.set(comment.author, flair_template_id='0e8e4996-604b-11ea-bd19-0eedcb93a73d')
            #     await self._channel.send("☣ Redditor u/{} was infected because of the {} by u/{}".format(
            #         comment.author.name,
            #         "comment" if type(infected_by) is models.Comment else "submission",
            #         "deleted" if not infected_by.author else infected_by.author.name
            #     ))
            #     comment.author.message(
            #         "☣ You were infected by the r/memes Memonavirus ☣",
            #         "Hey u/{},\n\nYou contracted the r/memes Memonavirus from u/{}! You contracted it because you commented on their {}, [linked here](https://www.reddit.com{}).\n\n## Don't know what this is about?\n\n[Check out this announcement to see what this is about!](https://www.reddit.com/r/memes/comments/cu5ep9/community_awards_yes_please/)".
            #         format(
            #             comment.author.name,
            #             infected_by.author.name,
            #             "comment" if type(infected_by) is models.Comment else "submission",
            #             infected_by.permalink
            #         )
            #     )

        except Exception as ex:
            logger.info("ERROR IN INFECT")
            logger.info(str(ex))
            pass



"""
"""
<div id="the-final-countdown">
  <p></p>
</div>
<script>
  setInterval(function time(){
  var d = new Date();
  var hours = 0;
  var min = 60 - d.getMinutes();
  if((min + '').length == 1){
    min = '0' + min;
  }
  var sec = 60 - d.getSeconds();
  if((sec + '').length == 1){
        sec = '0' + sec;
  }
  jQuery('#the-final-countdown p').html(min+':'+sec)
}, 1000);
</script>


@import url(https://fonts.googleapis.com/css?family=Lato:100,400);
#the-final-countdown {
  background: #333;
  font-family: 'Arial', sans-serif;
  text-align: center;
  color: #eee;
  text-shadow: 1px 1px 5px black;
  padding: 1rem 0;
  font-size: 3rem;
  border: 1px solid #000;
}


"""
