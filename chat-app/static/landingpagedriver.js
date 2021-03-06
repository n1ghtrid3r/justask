
const canvas = document.getElementById('canvas');
const context = canvas.getContext('2d');

const MAX_PARTICLE_VELOCITY = 1.5;
const particleRadius = 4;
const particleDistanceThreshold = 170;
const maxNeighbors = 3;
const PARTICLE_DISTANCE_THRESHOLD_SQ =  Math.pow(particleDistanceThreshold, 2)
const SPAWN_N_PARTICLES_ON_CLICK = 5;
const N_PARTICLES = 150;
const LINK_COLOR = "rgba(109,127,204,";
const BACKGROUND_COLOR= "rgba(255,255,255,255)";
const PARTICLE_COLOR = "rgba(185,127,13,";

let particles
function resizeCanvas() 
{
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    particles = GenerateParticles(N_PARTICLES);
    drawStuff(); 
}







// function testing()
// {

//     form = $('FORMID');
//     divToTarget = $('DIVTOTARGETID');
//     if(form.text() == ""){
//         divToTarget.css("visibility", "hidden");
//     }
// }

$('document').ready(function(){

    let loginBox = $('#loginBox');
    let registrationBox = $('#registrationBox');


    function ShowLoginBox()
    {
        // on click, make the login box visible.
        if (loginBox.css('opacity') == 1) return;
        loginBox.css('visibility', "visible");
        loginBox.css('opacity', 1)

        let welcome = $('#welcome');
        welcome.css('visibility', "hidden");
        if (registrationBox.css('opacity') == 0) return;
        registrationBox.css('opacity', '0')
        registrationBox.css('visibility', 'hidden');
        
    }

    function ShowRegistrationBox()
    {
        loginBox.css('opacity', 0)
        registrationBox.css("visibility", "visible");
        registrationBox.css("opacity", 1);
        loginBox.css('visibility', 'hidden');
        
    }

    function TogglePasswordVisibility(passwordFieldSelector){
        passwordField = $(passwordFieldSelector)
        if (passwordField.attr("type") === "password")  passwordField.attr("type", "text")
        else passwordField.attr("type", "password")
    }


    $('#view_login_password').click(function(){
        TogglePasswordVisibility("#password")
    })
    $('#view_registration_password').click(function(){
        TogglePasswordVisibility("#reg_password")
    })


    $(window).resize(resizeCanvas)

    $('#continue').click(ShowLoginBox)

    $('#signupLink').click(ShowRegistrationBox)
    $('#redirectToLogin').click(ShowLoginBox)
})





class Vector2f
{
    constructor(x,y)
    {
        this.x = x;
        this.y = y;
    }

}

class Particle
{
    constructor(posx, posy, velx, vely)
    {
        this.posx = posx;
        this.posy = posy;
        this.velx = velx;
        this.vely = vely;
    }
    AddPosition(x,y)
    {
        this.posx += x;
        this.posy+=y;
    }
}


function RandomNumberNegativeBounds(lowerBound, upperBound)
{
    return (Math.random()*(2*upperBound + 1)) - lowerBound 
}

function RandomNumber(lowerBound, upperBound)
{
    return lowerBound + (Math.random()*upperBound); 
}


function DistanceSq(particle1, particle2)
{
    return Math.pow(particle1.posx - particle2.posx, 2) + Math.pow(particle1.posy -particle2.posy, 2);
}
function Distance(particle1, particle2)
{
    return Math.sqrt(DistanceSq(particle1, particle2));
}





const maxX = window.innerWidth;
const maxY = window.innerHeight;




function GenerateParticle(posx, posy)
{
    return new Particle(posx, posy, RandomNumberNegativeBounds(-MAX_PARTICLE_VELOCITY, MAX_PARTICLE_VELOCITY), RandomNumberNegativeBounds(-MAX_PARTICLE_VELOCITY, MAX_PARTICLE_VELOCITY));

}
function GenerateParticles(numberofParticles)
{

    let particles = [];
    for(let i = 0; i < numberofParticles; ++i)
    {
        particles.push(GenerateParticle(RandomNumber(0,maxX), RandomNumber(0,maxY)))
    }
    return particles;
}



particles = GenerateParticles(N_PARTICLES);



function drawStuff() 
{
    // do your drawing stuff here
    requestAnimationFrame(drawStuff)
    context.fillStyle = BACKGROUND_COLOR;
    context.fillRect(0, 0, canvas.width, canvas.height);
    for(particleIndex in particles)
    {
        particle = particles[particleIndex];
        // particle.AddPosition(particle.velx, particle.vely);
        particle.posx += particle.velx;
        particle.posy += particle.vely;



        // clip the bounds of the particle so as to wrap around the screen.

        if(particle.posx < 0) particle.posx = maxX;
        else if (particle.posx > maxX) particle.posx = 0;
        if(particle.posy < 0) particle.posy = maxY;
        else if(particle.posy > maxY) particle.posy = 0;
        


        // now, for each particle, find the nearest particles and their distances from the current particle.
        const closestParticles = []
        const closestParticlesDistances = []

        for(otherParticleIndex in particles)
        {
            if(closestParticles.length >= maxNeighbors) break;
            if(particleIndex == otherParticleIndex) continue;
            var distSq = DistanceSq(particle, particles[otherParticleIndex])
            if(distSq < PARTICLE_DISTANCE_THRESHOLD_SQ)
            {
                // particle is in range
                closestParticles.push(otherParticleIndex);
                closestParticlesDistances.push(distSq);

            }

        }

        // for each of the particles in viscinity, draw a line from this particle to the current particle
        // proportional to the distance from that particle to the current particle.
        for(otherParticleIndex in closestParticles)
        {
            otherParticle = particles[closestParticles[otherParticleIndex]]
            let strokeOpacity = 1000/ closestParticlesDistances[otherParticleIndex];
            context.strokeStyle = LINK_COLOR + strokeOpacity.toString() + ")";
            context.moveTo(particle.posx, particle.posy);
            context.lineTo(otherParticle.posx, otherParticle.posy);
            context.stroke();
        }

        // render the particle.
        context.fillStyle = PARTICLE_COLOR;
        context.beginPath();
        context.arc(particle.posx, particle.posy, particleRadius, 0, 2 * Math.PI);
        context.fill();


    }

}


// resize the canvas to fill browser window dynamically
window.addEventListener('resize', resizeCanvas, false);
resizeCanvas();
    

function spawnParticles(canvas, event) {



    // spawn n particles given an event.
    const rect = canvas.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    
    for(let i = 0; i < SPAWN_N_PARTICLES_ON_CLICK; ++i)
    {
        let randomIndex = RandomNumber(0, particles.length);
        particles.splice(randomIndex, 1);
        particle = GenerateParticle(x,y);
        particles.push(particle);
    }
}


// every time the user clicks the mouse down, SPAWN_N_PARTICLES_ON_CLICK particles will be spawned with random properties.
canvas.addEventListener('mousedown', function(e) {
    spawnParticles(canvas, e)
})

