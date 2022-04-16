from flask import Flask, render_template, request,jsonify
from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from Logging import logger
import os.path
import sys
import time
from MongoDatabaseHandler import MongoDatabaseHandler

INEURON_URL="https://ineuron.ai/"

# database input
MONGO_DB_USERNAME = "test"
MONGO_DB_PWD = "test"
MONGO_DB = "IneuronScrapper"
MONGO_DB_COLLECTION = "CourseScrapper"


class IneuronScrapper:
    def __init__(self, courseScrapper):
        self.__app = Flask(__name__)
        self.__courseScrapper = courseScrapper
        self.__SetHomePageRoute()
        self.__SetCoursePageRoute()
        self.__SetSubCoursePageRoute()
        self.__SetCourseDetailsPageRoute()

    def Run(self, mode=False, port=5000):
        # open the chrome driver
        self.__courseScrapper.Initialize()
        # Start the Flask
        self.__app.run(debug=mode, port=port)

    def __SetHomePageRoute(self):
        @self.__app.route('/',methods=['GET'])  # route to display the home page
        @cross_origin()
        def homePage():
            return render_template("index.html")

    def __SetCoursePageRoute(self):
        @self.__app.route('/courses',methods=['GET'])  # route to display the home page
        @cross_origin()
        def coursePage():
            courses = self.__courseScrapper.GetCourses()
            return jsonify(courses)

    def __SetSubCoursePageRoute(self):
        @self.__app.route('/course/<courseName>', methods=['GET'])  # route to display the home page
        @cross_origin()
        def subCoursePage(courseName):
            subCourses = self.__courseScrapper.GetSubCourses(courseName)
            return jsonify(subCourses)

    def __SetCourseDetailsPageRoute(self):
        @self.__app.route('/courses/detail', methods=['GET'])  # route to display the home page
        @cross_origin()
        def subCourseDetailsPage():
            courseDetailsStatus = self.__courseScrapper.GetCoursesDetails()
            return jsonify(courseDetailsStatus)


class IneuronCourseScrapper:
    def __init__(self, url, driverPath, mongoDB):
        # raise exception if drive doesnt exist
        if False == os.path.exists(driverPath):
            raise Exception("Could not find Chrome Driver in Path [{}]".format(driverPath))
        # init the variable
        self.__url = url
        self.__chromeDriverPath = driverPath
        self.__mongoDB = mongoDB

    def __del__(self):
        self.__wd.close()
        pass

    def Initialize(self):
        try:
            self.__mongoDB.ConnectAndCreateDB()
        except Exception as db:
            logger.error(db)

        try:
            self.__wd = webdriver.Chrome(executable_path=self.__chromeDriverPath)
            self.__wd.maximize_window()
        except Exception as wd:
            logger.error(wd)


    def GetCourses(self):
        try:
            self.__MouseHoverCourses()

            # get page source
            coursePage = self.__wd.page_source

            # loadin the page source in beautifulsoup
            ineuronCourseHtml = bs(coursePage, "html.parser")

            # traversing the path
            categoriesDiv = ineuronCourseHtml.find("div", {"id": "categories-list"})
            categoriesList = categoriesDiv.findAll("li")

            # Getting the course details
            courseNameList = []
            for entry in categoriesList:
                courseNameList.append(entry.text.strip())

            # creating the json
            courseResult={}
            courseResult["Courses"] = courseNameList

            # returning the json
            return courseResult

        except Exception as e:
            logger.error(e)
            return {"Courses": []}

    def GetSubCourses(self, courseName):
        try:
            self.__MouseHoverCourses()

            # subcategory
            courseNameDiv = self.__wd.find_element_by_partial_link_text(courseName)
            action = ActionChains(self.__wd)
            action.move_to_element(courseNameDiv).perform()

            # get page source courseNameList
            subCoursePage = self.__wd.page_source

            # loading the page source in bsoup
            ineuronSubCourseHtml = bs(subCoursePage, "html.parser")

            # traversing the path
            subCategoriesDiv = ineuronSubCourseHtml.find("div", {"id": "subcategories-list"})
            subCategoriesList = subCategoriesDiv.findAll("li")

            # Getting the course details
            subCourseNameList = []
            for entry in subCategoriesList:
                subCourseNameList.append(entry.text.strip())

            # creating the json
            courseResult={}
            courseResult['Course'] = courseName
            courseResult["Sub-Courses"] = subCourseNameList

            # returning the json
            return courseResult

        except Exception as e:
            logger.error(e)
            return {"Courses": []}

    def GetCoursesDetails(self):
        try:
            self.__MouseHoverCourses()

            # get page source
            coursePage = self.__wd.page_source

            # loading the page source in bsoup
            ineuronCourseHtml = bs(coursePage, "html.parser")

            # traversing the path
            categoriesDiv = ineuronCourseHtml.find("div", {"id": "categories-list"})
            categoriesRefList = categoriesDiv.findAll("a")

            # Getting the course details
            courseNameList = []
            for entry in categoriesRefList:
                course_url = entry["href"]
                courseNameList.append(entry.text.strip())
                self.__wd.get(course_url)

                # time to load the home page with pop-up
                time.sleep(10)

                self.__ScrollToEnd()

                courseDetailPage = self.__wd.page_source

                ineuronCourseDetailsHtml = bs(courseDetailPage, "html.parser")

                AllCourses = ineuronCourseDetailsHtml.find("div", {"class": "AllCourses_course-list__36-kz"})
                coursesList = AllCourses.findAll("div", {"class": "Course_right-area__1XUfi"})

                coursesDetailsDict = {"FetchingCoursesDetails" : {"Status" : "Success"}}
                for entry in coursesList:
                    courseDetailDict = {}
                    specificCourseUrl = "https://courses.ineuron.ai" + entry.a["href"]

                    self.__wd.get(specificCourseUrl)
                    # time to load the home page with pop-up
                    time.sleep(10)

                    # closing the enquiry pop-up
                    self.__wd.find_element_by_xpath("//*[@id='Modal_enquiry-modal__CqkIq']/div/div[1]/i").click()

                    try:
                        # click the view more
                        self.__wd.find_element_by_xpath("//*[@id='__next']/section[2]/div/div/div[1]/div[3]/span/i").click()
                    except Exception as ex:
                        logger.error(ex)

                    pageSource = self.__wd.page_source

                    CourseDetailsHtml = bs(pageSource, "html.parser")

                    courseHeroLeftDiv = CourseDetailsHtml.find("div", {"class": "Hero_left__2v34v"})

                    atag = courseHeroLeftDiv.div.findAll("a")

                    #################### Course ####################
                    courseName = atag[0].text
                    courseDetailDict["Course"] = courseName

                    #################### Sub Course ####################
                    subCourseName = atag[1].text
                    courseDetailDict["Sub-Course"] = subCourseName

                    #################### Course Title ####################
                    courseDetailsTitle = courseHeroLeftDiv.find("h3").text
                    courseDetailDict["Course-Title"] = courseDetailsTitle

                    #################### Description ####################
                    description = courseHeroLeftDiv.find("div", {"class": "Hero_course-desc__26_LL"}).text
                    courseDetailDict["Description"] = description

                    #################### Price ####################
                    try:
                        price = CourseDetailsHtml.find("div", {"class": "CoursePrice_dis-price__3xw3G"}).span.text
                        courseDetailDict["Price"] =  price[1:]
                    except Exception as pe:
                        logger.warning("Exception: Parsing Course Price [{}]".format(pe))

                    # metadata
                    metadata = CourseDetailsHtml.find("div", {"class": "CourseMeta_course-batch-content__1BsUU CourseMeta_flex__1wVzO flex"})

                    #################### What you learn ####################
                    try:
                        whatYouLearn = metadata.find("div", {"class": "CourseLearning_card__WxYAo card"}).findAll("li")

                        whatYouLearnList = []
                        for learn in whatYouLearn:
                            whatYouLearnList.append(learn.text)

                        courseDetailDict["What_You_Will_Learn"] = whatYouLearnList
                    except Exception as wyl:
                        logger.warning("Exception: Parsing Course What You Will Learn [{}]".format(wyl))

                    #################### Requirements ####################
                    try:
                        requirements = metadata.find("div",
                                                     {"class": "CourseRequirement_card__3g7zR requirements card"}).findAll(
                            "li")

                        reqList = []
                        for req in requirements:
                            reqList.append(req.text)

                        courseDetailDict["Requirements"] = reqList
                    except Exception as cr:
                        logger.warning("Exception: Parsing Course Requirements [{}]".format(cr))

                    #################### Course Feature ####################
                    try:
                        courseFeature = metadata.find("div", {"class": "CoursePrice_course-features__2qcJp"}).findAll("li")

                        courseFeatureList = []
                        for feature in courseFeature:
                            courseFeatureList.append(feature.text)

                        courseDetailDict["Course_Feature"] = courseFeatureList

                    except Exception as cf:
                        logger.warning("Exception: Parsing Course Feature [{}]".format(cf))


                    #################### Curriculam ####################
                    try:
                        projectCurriculamList = metadata.findAll("div", {
                            "class": "CurriculumAndProjects_curriculum-accordion__2pppc CurriculumAndProjects_card__7HqQx card"})

                        curriculumDict = {}
                        for projectCurriculam in projectCurriculamList:
                            clist = []
                            curriculumList = projectCurriculam.findAll("ul")
                            for currRef in curriculumList:
                                for li in currRef.findAll("li"):
                                    clist.append(li.text)
                            curriculumDict[projectCurriculam.span.text] = clist

                        courseDetailDict["Course_Curriculum"] = curriculumDict

                    except Exception as ce:
                        logger.warning("Exception: Parsing Course Feature [{}]".format(ce))

                    #################### Instructor ####################

                    try:
                        instructor = metadata.findAll("div", {"class": "InstructorDetails_left__3jo8Z"})

                        instructorList = []
                        for name in instructor:
                            instructorList.append(name.h5.text)

                        courseDetailDict["Instructors"] = instructorList

                    except Exception as ie:
                        logger.warning("Exception: Parsing Course Feature [{}]".format(ie))

                    # publish data to DB
                    self.__mongoDB.InsertOneData(courseDetailDict)

            # returning the json
            return coursesDetailsDict

        except Exception as e:
            logger.error(e)
            return {"FetchingCoursesDetails" : {"Status": "Failed"}}

    def __MouseHoverCourses(self):
        try:
            # load the URL in chrome browser
            self.__wd.get(self.__url)

            # time to load the home page with pop-up
            time.sleep(15)

            # closing the enquiry pop-up
            self.__wd.find_element_by_xpath("//*[@id='enquiry-modal']/div/div[1]/i").click()

            # time to close the pop-up
            time.sleep(2)

            # mouse hover the course drop down
            courseDropDown = self.__wd.find_element_by_class_name("dropdown-chevron-down")

            # mouse hovering
            action = ActionChains(self.__wd)
            action.move_to_element(courseDropDown).perform()

        except Exception as mhc:
            logger.error("Exception: Mouse Hover Courses [{}]".format(mhc))


    def __ScrollToEnd(self):
        old_len = 0
        while (True):
            new_len = self.__wd.execute_script(
                "window.scrollTo(0, document.body.scrollHeight); return document.body.scrollHeight")
            if new_len != old_len:
                old_len = new_len
                time.sleep(1)
            else:
                break

logger.info("Ineuron Course Scrapper Application - Started")

try:
    # chrome drive should be in current directory
    cwd = os.getcwd()
    chromeDrivePath = cwd + '\\' + "chromedriver.exe"
    mongoDB = MongoDatabaseHandler(MONGO_DB_USERNAME, MONGO_DB_PWD, MONGO_DB, MONGO_DB_COLLECTION)
    courseScrapper = IneuronCourseScrapper(INEURON_URL, chromeDrivePath, mongoDB)
except Exception as e:
    logger.error("Exception: In main [{}]".format(e))
    sys.exit(0)
else:
    scrapperInstance = IneuronScrapper(courseScrapper)

if __name__ == "__main__":
    logger.info("Init Success, Course Scrapper - Started")
    scrapperInstance.Run()
