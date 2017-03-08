from django.db import models
from django.shortcuts import HttpResponse, render

class Experiment(models.Model):
    def __str__(self):
        try:
            return self.name
        except:
            return 'experiment'
    """
    """
    name = models.CharField(max_length=255, null=True, blank=True)

    def render(self, request, context):
        ex = self
        userTest = None
        if not request.COOKIES.get('e_'+str(ex.pk),''): #user hasn't been assigned a test for the experiment
            tests = ex.tests.all()
            if tests.count() > 0: #make sure there is a test
                userTest = tests[0] #usersTest is going to be the test with the minimum hits
                for test in tests: #find the min usersTest.hits
                    if test.hits < userTest.hits:
                        userTest = test
                userTest.hits += 1
                userTest.save()
            else:
                raise Exception('No Tests For this Experiment')
        else:
            userTest = Test.objects.get(pk=request.COOKIES.get('e_'+str(ex.pk),''))
        response = render(request, userTest.template_name, context)
        response.set_cookie( 'e_'+str(ex.pk), str(userTest.pk), max_age=3600*24*365)
        return response

    def getTemplateName(self, request, response):
        '''This basically assigns everyone to a test for every expirement. Tests are assigned into cookies.
            The cookie will have the name of e_13 meaning the expiriment's pk is 13 and the value of that cookie
            will be the pk of the test. If the user doesn't have a cookie for an expiriment then we assign them one
            based on whichever test in that experiment has the least number of hits.
        '''
        ex = self
        if not response:
            response = HttpResponse
        if not request.COOKIES.get('e_'+str(ex.pk),''): #user hasn't been assigned a test for the experiment
            tests = ex.tests.all()
            if tests.count() > 0: #make sure there is a test
                usersTest = tests[0] #usersTest is going to be the test with the minimum hits
                for test in tests: #find the min usersTest.hits
                    if test.hits < usersTest.hits:
                        usersTest = test
                response
                response.set_cookie( 'e_'+str(ex.pk), str(usersTest.pk), max_age=3600*24*365)
                usersTest.hits += 1
                usersTest.save()
        else:
            test = Test.objects.get(pk=request.COOKIES.get('e_'+str(ex.pk),''))
        return test.template_name

    def achieveGoal(self, request, response):
        '''
        This looks at the experiment and makes sure that it is the first time that they have achieved that
         experiments goal. If it's the first time the user has reached the goal, then we increment the
         conversion counter for the test and set the achieved cookie for that experiment.
        '''
        #check to see if we have hit any of our goals:
        ex = self
        if not request.COOKIES.get('achieved_'+str(ex.pk),''): #make sure we haven't already achieved this goal
            test_pk = request.COOKIES.get('e_'+str(ex.pk),'')
            if test_pk:
                print('reached a goal')
                test = ex.tests.get(pk = test_pk)
                test.conversions += 1
                test.save()
                response.set_cookie( 'achieved_'+str(ex.pk), 'yes', max_age=3600*24*365)

class Test(models.Model):
    experiment = models.ForeignKey(Experiment, related_name='tests')

    template_name = models.CharField(max_length=255,
        help_text="Example: 'signup_1.html'. The template to be tested.")
    hits = models.IntegerField(default=0, 
        help_text="# uniques that have seen this template.")
    conversions = models.IntegerField(default=0,
        help_text="# uniques that have reached the goal from this test.")
    
    def __str__(self):
        try:
            return self.name
        except:
            return self.template_name


    
