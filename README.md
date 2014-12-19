RobertsAB
=========

A super small and simple django app for AB testing various templates.

Usage
------

Include RobertsAB inside your installed apps:

    INSTALLED_APPS = (
        'RobertsAB',
        ...
    )

Then call `./manage.py syncdb` or `migrate` or whatever they want us to do now.


Go into the admin and create your first Expiriment. 

An Experiment is basically just a group of Tests with a name. For example maybe you want to test 3 landing pages with different color backgrounds. You might create an Experiment called `landingColor`. And give it three tests with different template names. `landingPageGreen.html` `landingPageRed.html` and `landingPageBlack.html`. Make sure your regular `TEMPLATE_LOADER` can find these templates.


Instead of rendering your template with `render` or `render_to_response` use the `render` method on the `Experiment` object

    def landingPage(request, error_msg=''):
        exp = Experiment.objects.get(name='landingColor')
        return exp.render(request, {})

or

    def landingPage(request, error_msg=''):
        exp = Experiment.objects.get(name='landingColor')
        random = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(16))
        return exp.render(request, {
            'error_msg': error_msg,
            'random': random,
        })

Rendering your template with the experiments render method will assign the user a Test and set some cookies to keep track of which Test they have been assigned, and consequently, which template will be rendered (until the user deletes their cookies and gets a new Test issued).

AB tests need to have a Goal. We are testing to see which template accomplishes our goal. Somewhere in your code you should call the `achieveGoal(request, response)` method on the experiment object.

for example in your `userDidSignUpAndPayUsATonOfMoney` view:

    def userDidSignUpAndPayUsATonOfMoney(request):
        ...
        exp = Experiment.objects.get(name='landingColor')
        exp.achieveGoal(request, response)
        return HttpResponse('Congratulations, you are signed up for lolcat!')

Calling this method will check to make sure our user hasn't already achieved this goal, and then increment our conversions count. 

When you are done. Open up your landingPage then clear the cookies and do it again, then do it a third time. You should see your different templates being loaded and see Test.hits being incremented in the admin.

If you have any questions you can open an issue or email me directly at crobertsbmw (gmail).