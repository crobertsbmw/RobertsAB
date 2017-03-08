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

Then call `./manage.py migrate`.


I know this is a little weird, but now go into the admin panel to create your first `Experiment`.

An Experiment is basically just a group of Tests with a name. For example maybe you want to test 3 landing pages with different color backgrounds. You might create an Experiment called `landingColor`. And give it three tests with different template names. `landingPageGreen.html` `landingPageRed.html` and `landingPageBlack.html`. Make sure your regular `TEMPLATE_LOADER` can find these templates.


Instead of rendering your template with `render` or `render_to_response` use the `render` method on the `Experiment` object

    def landingPage(request):
        exp = Experiment.objects.get(name='landingColor')
        return exp.render(request, {})


Rendering your template with the experiment's `render` method will assign the user a `Test` and set some cookies to keep track of which `Test` they have been assigned, and consequently, which template will be rendered (until the user deletes their cookies and gets a new Test issued).

AB tests need to have a Goal. We are testing to see which template accomplishes our goal. Somewhere in your code you should call the `achieveGoal(request, response)` method on the experiment object.

for example in your `userDidSignUpAndPayUsATonOfMoney` view:

    def userDidSignUpAndPayUsATonOfMoney(request):
        ...
        exp = Experiment.objects.get(name='landingColor')
        response = HttpResponse('Congratulations, you are signed up for hourly spam in your inbox!')
        exp.achieveGoal(request, response)
        return response

Calling this method will check to make sure our user hasn't already achieved this goal, and then increment our conversions count. 

When you are done. Open up your landingPage then clear the cookies and do it again, then do it a third time. You should see your different templates being loaded and see `Test.hits` being incremented in the admin panel.

This works to AB test your system. You will have to open up your admin panel to see the results of the test and draw your own conclusions.
